Name:		jna-platform
Version:	5.19.1
Release:	1
Summary:	Platform mappings for Java Native Access
Group:		Development/Java
License:	(LGPL-2.1-or-later OR Apache-2.0)
URL:		https://github.com/java-native-access/jna
Source0:	https://codeload.github.com/java-native-access/jna/tar.gz/refs/tags/%{version}#/jna-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	python
BuildRequires:	sysjar
BuildRequires:	mvn(net.java.dev.jna:jna)

%description
Platform-specific JNA interface mappings. This jar is built from the
upstream platform Java sources and calls through the system jna
package. It ships no native library of its own.

%prep
%setup -q -n jna-%{version}
# The tag archive carries prebuilt jars, native libraries and a signing key.
rm -rf dist lib native www test build src
rm -f jna.keystore
find . -name '*.class' -delete
find . -name '*.jar' -delete
find . \( -name '*.so' -o -name '*.dll' -o -name '*.jnilib' -o -name '*.dylib' \) -delete
if find . \( -name '*.class' -o -name '*.jar' -o -name '*.so' -o -name '*.dll' \) | grep -q .; then
	echo "prebuilt bytecode remains" >&2
	exit 1
fi

%build
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
mkdir -p build/classes
find contrib/platform/src -name '*.java' > build/sources.list
test "$(wc -l < build/sources.list)" -eq 246
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 \
	-cp /usr/share/java/jna.jar \
	-d build/classes @build/sources.list
python - build/classes << 'PY'
import os
import sys
root = sys.argv[1]
count = 0
for dirpath, _, files in os.walk(root):
    for name in files:
        if not name.endswith(".class"):
            continue
        count += 1
        data = open(os.path.join(dirpath, name), "rb").read(8)
        major = int.from_bytes(data[6:8], "big")
        if major != 52:
            raise SystemExit("class " + name + " has major " + str(major))
if count != 1333:
    raise SystemExit("class count " + str(count))
PY
find contrib/platform/src -name '*.template' > build/templates.list
test "$(wc -l < build/templates.list)" -eq 11
while IFS= read -r template; do
	rel=${template#contrib/platform/src/}
	install -D -m 644 "$template" "build/classes/$rel"
done < build/templates.list
cat > build/manifest.mf << EOF
Manifest-Version: 1.0
Implementation-Title: com.sun.jna.platform
Implementation-Vendor: JNA Development Team
Implementation-Version: %{version}
Specification-Title: Java Native Access Platform
Specification-Vendor: JNA Development Team
Specification-Version: %{version}
Automatic-Module-Name: com.sun.jna.platform

EOF
"$JAVA_HOME/bin/jar" --create --manifest build/manifest.mf \
	--file build/jna-platform.jar -C build/classes .
cat > build/jna-platform.pom << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>net.java.dev.jna</groupId>
  <artifactId>jna-platform</artifactId>
  <version>%{version}</version>
  <name>Java Native Access Platform</name>
  <description>Platform mappings for Java Native Access, built against the system jna jar.</description>
  <url>https://github.com/java-native-access/jna</url>
  <licenses>
    <license><name>LGPL-2.1-or-later</name></license>
    <license><name>Apache-2.0</name></license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>net.java.dev.jna</groupId>
      <artifactId>jna</artifactId>
      <version>%{version}</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact build/jna-platform.pom:build/jna-platform.jar \
	--alias net.java.dev.jna:platform \
	--file-name jna-platform \
	--filelist .mfiles

%check
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
"$JAVA_HOME/bin/jar" tf build/jna-platform.jar > build/jar-list.txt
grep -qx 'com/sun/jna/platform/linux/LibC.class' build/jar-list.txt
grep -qx 'com/sun/jna/platform/win32/Kernel32.class' build/jar-list.txt
grep -qx 'com/sun/jna/platform/win32/COM/tlb/imp/TlbCoClass.template' build/jar-list.txt
test "$(grep -c '\.template$' build/jar-list.txt)" -eq 11
if grep -E '\.(so|dll|jnilib|jar)$' build/jar-list.txt; then
	echo "jar contains a native library or a nested jar" >&2
	exit 1
fi
"$JAVA_HOME/bin/jar" --describe-module --file build/jna-platform.jar > build/module.txt
grep -F 'com.sun.jna.platform automatic' build/module.txt
cat > build/Probe.java << 'EOF'
import com.sun.jna.platform.linux.LibC;

public class Probe {
    public static void main(String[] args) {
        LibC.Sysinfo info = new LibC.Sysinfo();
        int rc = LibC.INSTANCE.sysinfo(info);
        if (rc != 0) {
            throw new AssertionError("sysinfo rc " + rc);
        }
        if (info.uptime.longValue() <= 0) {
            throw new AssertionError("uptime " + info.uptime.longValue());
        }
        System.out.println("probe ok");
    }
}
EOF
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 \
	-cp "build/jna-platform.jar:/usr/share/java/jna.jar" \
	-d build build/Probe.java
# jna.nosys defaults to false in the system jna jar, so libjnidispatch.so
# is loaded from the JVM library path. A noarch build's %{_libdir} is
# /usr/lib and does not contain that 64-bit library.
"$JAVA_HOME/bin/java" --enable-native-access=ALL-UNNAMED \
	-cp "build:build/jna-platform.jar:/usr/share/java/jna.jar" \
	Probe > build/probe.txt
cat build/probe.txt
grep -qx 'probe ok' build/probe.txt

%files -f .mfiles
%license LICENSE AL2.0 LGPL2.1
%doc README.md CHANGES.md

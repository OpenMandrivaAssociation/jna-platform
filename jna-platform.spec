Name:		jna-platform
Version:	5.19.1
Release:	2
Summary:	Platform mappings for Java Native Access
Group:		Development/Java
License:	(LGPL-2.1-or-later OR Apache-2.0)
URL:		https://github.com/java-native-access/jna
Source0:	https://codeload.github.com/java-native-access/jna/tar.gz/refs/tags/%{version}#/jna-%{version}.tar.gz
Source1:	https://codeload.github.com/java-native-access/jna/tar.gz/refs/tags/5.17.0#/jna-5.17.0.tar.gz
BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	python
BuildRequires:	sysjar
BuildRequires:	mvn(net.java.dev.jna:jna)

%description
Platform-specific JNA interface mappings. This jar is built from the
upstream platform Java sources and calls through the system jna
package. It ships no native library of its own. The 5.17.0 jar is
installed beside %{version}. Gradle 9.9.1 strictly requests 5.17.0.

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
%setup -q -T -D -a 1 -n jna-%{version}
find jna-5.17.0 \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' -o -name '*.dll' \) -delete
rm -rf jna-5.17.0/dist jna-5.17.0/lib jna-5.17.0/native jna-5.17.0/www jna-5.17.0/test jna-5.17.0/build jna-5.17.0/src

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
mkdir -p jna517/classes
find jna-5.17.0/contrib/platform/src -name '*.java' > jna517/sources.list
test "$(wc -l < jna517/sources.list)" -eq 241
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp /usr/share/java/jna.jar \
	-d jna517/classes @jna517/sources.list
python - jna517/classes << 'PY'
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
if count != 1285:
    raise SystemExit("class count " + str(count))
PY
find jna-5.17.0/contrib/platform/src -name '*.template' > jna517/templates.list
test "$(wc -l < jna517/templates.list)" -eq 11
while IFS= read -r template; do
	rel=${template#jna-5.17.0/contrib/platform/src/}
	install -D -m 644 "$template" "jna517/classes/$rel"
done < jna517/templates.list
cat > jna517/manifest.mf << 'EOF'
Manifest-Version: 1.0
Implementation-Title: com.sun.jna.platform
Implementation-Vendor: JNA Development Team
Implementation-Version: 5.17.0
Specification-Title: Java Native Access Platform
Specification-Vendor: JNA Development Team
Specification-Version: 5.17.0
Automatic-Module-Name: com.sun.jna.platform

EOF
"$JAVA_HOME/bin/jar" --create --manifest jna517/manifest.mf \
	--file jna517/jna-platform.jar -C jna517/classes .
cat > jna517/jna-platform.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>net.java.dev.jna</groupId>
  <artifactId>jna-platform</artifactId>
  <version>5.17.0</version>
  <name>Java Native Access Platform</name>
  <description>Platform mappings from the JNA 5.17.0 tag, built against the system jna jar.</description>
  <url>https://github.com/java-native-access/jna</url>
  <licenses>
    <license><name>LGPL-2.1-or-later</name></license>
    <license><name>Apache-2.0</name></license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>net.java.dev.jna</groupId>
      <artifactId>jna</artifactId>
      <version>5.19.1</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact jna517/jna-platform.pom:jna517/jna-platform.jar \
	--file-name jna-platform-5.17.0 \
	--filelist .mfiles517
# %{version} owns jna-platform.sysjar. 5.17.0 keeps a second index file.
/bin/mv %{buildroot}/usr/share/sysjar/index/net.java.dev.jna/jna-platform.sysjar \
	%{buildroot}/usr/share/sysjar/index/net.java.dev.jna/jna-platform-5.17.0.sysjar
sed -i 's|/usr/share/sysjar/index/net.java.dev.jna/jna-platform\.sysjar|/usr/share/sysjar/index/net.java.dev.jna/jna-platform-5.17.0.sysjar|' .mfiles517
sysjar install --buildroot %{buildroot} \
	--artifact build/jna-platform.pom:build/jna-platform.jar \
	--alias net.java.dev.jna:platform \
	--file-name jna-platform \
	--filelist .mfiles
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles517

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
sed 's/probe ok/probe517 ok/' build/Probe.java > build/Probe.java.new
/bin/mv build/Probe.java.new build/Probe.java
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 \
	-cp "%{buildroot}%{_javadir}/jna-platform-5.17.0.jar:/usr/share/java/jna.jar" \
	-d build build/Probe.java
"$JAVA_HOME/bin/java" --enable-native-access=ALL-UNNAMED \
	-cp "build:%{buildroot}%{_javadir}/jna-platform-5.17.0.jar:/usr/share/java/jna.jar" \
	Probe > build/probe517.txt
cat build/probe517.txt
grep -qx 'probe517 ok' build/probe517.txt

%files -f .mfiles
%license LICENSE AL2.0 LGPL2.1
%doc README.md CHANGES.md

from pathlib import Path
from xml.etree import ElementTree as ET

# NB: Copied from javadoc-wrangler and status.scijava.org
# Make this into a shared Python library for working with Maven POMs.
# Or: part of jgo??


class XML:
    """
    An object housing an ElementTree with convenience functions.
    """

    def __init__(self, source):
        if isinstance(source, str) and source.startswith('<'):
            # Parse XML from string.
            # https://stackoverflow.com/a/18281386/1207769
            self.tree = ET.ElementTree(ET.fromstring(source))
        else:
            # Parse XML from file.
            self.tree = ET.parse(source)
        XML._strip_ns(self.tree.getroot())

    def elements(self, path):
        return self.tree.findall(path)

    def value(self, path):
        el = self.elements(path)
        assert len(el) <= 1
        return None if len(el) == 0 else el[0].text

    @staticmethod
    def _strip_ns(el):
        """
        Remove namespace prefixes from elements and attributes.
        Credit: https://stackoverflow.com/a/32552776/1207769
        """
        if el.tag.startswith("{"):
            el.tag = el.tag[el.tag.find("}")+1:]
        for k in list(el.attrib.keys()):
            if k.startswith("{"):
                k2 = k[k.find("}")+1:]
                el.attrib[k2] = el.attrib[k]
                del el.attrib[k]
        for child in el:
            XML._strip_ns(child)

class MavenPOM(XML):

    @property
    def groupId(self) -> Optional[str]:
        return self.value("groupId") or self.value("parent/groupId")

    @property
    def artifactId(self) -> Optional[str]:
        return self.value("artifactId")

    @property
    def version(self) -> Optional[str]:
        return self.value("version") or self.value("parent/version")

    @property
    def scmURL(self) -> Optional[str]:
        return self.value("scm/url")

    @property
    def issuesURL(self) -> Optional[str]:
        return self.value("issueManagement/url")

    @property
    def ciURL(self) -> Optional[str]:
        return self.value("ciManagement/url")

    @property
    def developers(self) -> List[Dict[str, Any]]:
        devs = []
        for el in self.elements("developers/developer"):
            dev: Dict[str, Any] = {}
            for child in el:
                if len(child) == 0:
                    dev[child.tag] = child.text
                else:
                    if child.tag == 'properties':
                        dev[child.tag] = {grand.tag: grand.text for grand in child}
                    else:
                        dev[child.tag] = [grand.text for grand in child]
            devs.append(dev)
        return devs

class MavenMetadata(XML):

    @property
    def groupId(self) -> Optional[str]:
        try:
            return self.value("groupId")
        except Exception:
            return self.value("parent/groupId")

    @property
    def artifactId(self) -> Optional[str]:
        return self.value("artifactId")

    @property
    def lastUpdated(self) -> Optional[int]:
        result = self.value("versioning/lastUpdated")
        return None if result is None else int(result)

    @property
    def latest(self) -> Optional[str]:
        # WARNING: The <latest> value is often wrong, for reasons I don't know.
        # However, the last <version> under <versions> has the correct value.
        # Consider using lastVersion instead of latest.
        return self.value("versioning/latest")

    @property
    def lastVersion(self) -> Optional[str]:
        vs = self.elements("versioning/versions/version")
        return None if len(vs) == 0 else vs[-1].text

    @property
    def release(self) -> Optional[str]:
        return self.value("versioning/release")

class MavenComponent:

    def __init__(self, g: str, a: str):
        self.groupId = g
        self.artifactId = a
        self.release = MavenComponent._metadata(release_repos, g, a)
        self.snapshot = MavenComponent._metadata(snapshot_repos, g, a)
        self.pom: Optional[MavenPOM] = None
        if self.snapshot and self.snapshot.lastVersion:
            # Get the newest POM possible, based on last updated SNAPSHOT.
            self.pom = MavenComponent._pom(snapshot_repos, g, a, v=self.snapshot.lastVersion,
                ts=str(self.snapshot.lastUpdated))
        elif self.release and self.release.lastVersion:
            # Get the POM of the newest release.
            self.pom = MavenComponent._pom(release_repos, g, a, v=self.release.lastVersion)

    @staticmethod
    def _metadata(repos: Sequence[str], g: str, a: str) -> Optional[MavenMetadata]:
        suffix = f"{g.replace('.', '/')}/{a}/maven-metadata.xml"
        best = None
        for repo in repos:
            path = f"{storage}/{repo}/{suffix}"
            if os.path.exists(path):
                m = MavenMetadata(path)
                if best is None or (m.lastUpdated is not None and m.lastUpdated > best.lastUpdated):
                    best = m
        return best

    @staticmethod
    def _pom(repos, g: str, a: str, v: str, ts=None) -> Optional[MavenPOM]:
        gav_path = f"{g.replace('.', '/')}/{a}/{v}"
        if v.endswith("-SNAPSHOT"):
            # Find snapshot POM with matching timestamp.
            assert ts is not None
            dt_requested = ts2dt(ts)
            pom_prefix = f"{a}-{v[:-9]}" # artifactId-version minus -SNAPSHOT
            for repo in repos:
                d = pathlib.Path(f"{storage}/{repo}/{gav_path}")
                for f in d.glob(f"{pom_prefix}-*.pom"):
                    m = re.match(pom_prefix + "-(\d{8}\.\d{6})-\d+\.pom", f.name)
                    if not m: continue # ignore weirdly named POM
                    dt_actual = ts2dt(m.group(1))
                    if abs(dt_requested - dt_actual).seconds <= ts_allowance:
                        # Timestamp is within tolerance! Found it!
                        return MavenPOM(str(f))
        else:
            # Find release POM.
            suffix = f"{gav_path}/{a}-{v}.pom"
            for repo in repos:
                path = f"{storage}/{repo}/{suffix}"
                if os.path.exists(path):
                    return MavenPOM(path)
        return None



pom = '/Users/curtis/.m2/repository/org/scijava/pom-scijava/'
xml = XML(pom)
parent = GAV(xml.value("parent/groupId"),
             xml.value("parent/artifactId"),
             xml.value("parent/version"))


THIS WORKS:
- mvn help:effective-pom -f ~/.m2/repository/net/imagej/imagej/2.5.0/imagej-2.5.0.pom

=== USES OF THIS THING ===

- javadoc.scijava.org
 -- download javadoc JARs corresponding to dependency versions in a pom-scijava release

- status.scijava.org
 -- harvest and aggregate metadata about Maven components

- melting pot
 -- 

- mega melt
 -- make a project including ALL components from a given pom-scijava BOM -- then melting-pot it

- command line
 -- list dependency versions of a given pom-scijava BOM
 -- list dependency versions of a given GAV generally
 -- "rough diamond dependency" detection: report when two dependencies of a project depend on different major versions of the same GA

- jgo
 -- synthesize environment of JAR files in a single directory
 -- optionally, run main method
 -- [cjdk] download and cache JDK + Maven somewhere

=== NEEDED FUNCTIONS ===

- given a POM file: give me a Python object I can use to interrogate it
- given a GAV: obtain and cache the POM file

=== REQUIREMENTS ===

- SPEED
 -- AS FAST AS POSSIBLE because we will be querying many GAVs to perform some of these operations
 -- BUT: slow is OK as needed, as long as we CACHE results locally (~/.m2/repository)

=== OPERATIONS ===

- [PATH] give me the local path to a Maven GAV(C)(P)
 -- always local, always a file
 -- if not existing: [RETRIEVE AND CACHE] it
  --- two ways to retrieve:
   ---- via requests
   ---- via `mvn dependency:get`
 -- IF we are on the same machine as a remote Maven repository, esp. Nexus 2, we can use the backing storage path directly, fast and snazzy

- [OPEN POM] given a path -- or a GAV(C)(P) via [PATH] op -- make a Python object with its contents
 -- flag for whether to open it RAW (as is) or INTERPOLATED (feed it through mvn help:effective-pom)
  --- If INTERPOLATED: should we cache the result? In theory it could differ over time due to profiles, but... that is evil. So yeah, we should do it.

- [DEPENDENCIES] get list of dependencies for a given POM
 -- probably want to OPEN POM INTERPOLATED first, then just rip out the <dependencies> as new GAV objects

- [GA METADATA] get/read a maven-metadata.xml
 -- useful for queries like "what release versions exist" and "what is the newest release version" and "what is the latest snapshot version"

- [BUILD ENVIRONMENT]
 -- see jgo

- [RUN A MAIN ENTRY POINT WITH ENVIRONMENT]
 -- jgo currently conflates main entry points with environments... should we decouple this?
  --- would still be fine for each environment to have a default entry point...


---------------------

class Context:
    """
    Stateful query system.
    - Java configuration: path to JRE/JDK.
    - Maven configuration:
      - path to Maven
      - path to settings.xml
      - path to Maven local repository cache
      - list of remote repositories to include

    Maven/Context object - corresponds to the application/query context
    - can add remote repositories.
    - can add paths to direct Maven repository storage.
    - can set the location of the local Maven repository cache (~/.m2/repository).
    - can set the location of a settings.xml for use with mvn queries.
    - can ask for a Project object for any groupId:artifactId: returns Project
    """
    def __init__(self
    pass


class Project:
    """
    Project object - corresponds to a groupId:artifactId (GA)
    - retrieves and caches the maven-metadata.xml 
    - can ask for available release and/or snapshot versions: returns Version object.
    """

    def __init__(self, groupId: str, artifactId: str):
        self.groupId = groupId
        self.artifactId = artifactId

    def __str__(self):
        return f"{self.groupId}:{self.artifactId}"

    def version(self, version: str) -> Version:
        return Version(self.groupId, self.artifactId, version)


class Version:
    """
    Version object - corresponds to a groupId:artifactId:version (GAV)
    - can ask for artifact of given classifier (default None for main) and packaging (default 'jar')
    - can ask for list of dependencies: returns List[Artifact]
    """

    def __init__(self, groupId: str, artifactId: str, version: str):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version

    def __str__(self):
        return f"{self.groupId}:{self.artifactId}:{self.version}"

    def artifact(self, classifier: str = None, packaging: str = "jar"):
        return Artifact(self.groupId, self.artifactId, self.version, classifier, packaging)


class Artifact:
    """
    Artifact object - corresponds to a groupId:artifactId:version:classifier:packaging (GAVCP)
    - can ask for the path to the artifact file -- resolved/downloaded on demand -- returns pathlib.Path
    """

    def __init__(self, groupId: str, artifactId: str, version: str, classifier: str = None, packaging: str = "jar"):
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.classifier = classifier
        self.packaging = packaging

    @staticmethod
    def from_gav(gav: str):
        s = gav.split(":")
        if 3 <= len(s) <= 5: return Artifact(*s)
        raise ValueError(f"Invalid GAV: {gav}")

    def __str__(self):
        gav = f"{self.groupId}:{self.artifactId}:{self.version}"
        return gav if self.classifier is None and self.packaging == "jar" \
                   else f"{gav}:{self.classifier or '(main)'}:{self.packaging}"


class Environment:
    """
    Environment object - corresponds to a list of artifacts:
    - constructed with list of *included* artifacts, and *excluded* artifacts
    - also has a dependency resolution strategy -- default/Maven, versus managed/scope-import
    - can specify a path where the environment should be *materialized*
    - can ask for an ID (hash) describing the environment uniquely
    - what about main method entry points? TODO
    """

    def __init__(self, included: List[Artifact], excluded: List[Artifact] = None, **kwargs):
        self.included = [] if included is None else included
        self.excluded = [] if excluded is None else excluded
        self.config = kwargs

    @staticmethod
    def from_endpoint(endpoint: str):
        included = []
        excluded = []
        for artifact_string in endpoint.split("+")
            if artifact_string.startswith("!"):
                excluded.append(Artifact.from_gav(artifact_string[1:]))
            else:
                included.append(Artifact.from_gav(artifact_string))
        return Environment(included, excluded)


    @property
    def endpoint(self):
        endpoint = "+".join(map(str, self.included))
        for artifact in self.excluded: endpoint += f"+!{artifact}"
        return endpoint

    def __str__(self):
        return self.endpoint

    @property
    def id(self):
        # TODO: hashcode for included and excluded lists -- just hash the string rep?
        pass

    def materialize(self, path: Path, **kwargs)
        # TODO: link/copy style: copy vs hard vs soft
        # TODO: Maven resolution strategy: naive vs managed
        pass

"""Topology sanity checks on generated CIM.

Catches the failure modes seen in PLN's existing aggregate file:

* dangling internal references
* duplicate rdf:ID
* degree-1 connectivity nodes (equipment attached to nothing)
* one node swallowing a whole substation (the degree-58 node in the PoC file)

These run on the emitted XML rather than on in-memory objects, so they also
catch serialisation mistakes.
"""

from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from pathlib import Path

# A busbar legitimately collects many bays. Beyond this, a node is more likely
# a modelling mistake than a real busbar.
BUSBAR_DEGREE_LIMIT = 40


@dataclass
class TopologyReport:
    objects: int = 0
    references: int = 0
    dangling: list[str] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    degree: dict[str, int] = field(default_factory=dict)
    node_names: dict[str, str] = field(default_factory=dict)
    isolated: list[str] = field(default_factory=list)
    oversized: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.dangling or self.duplicate_ids or self.oversized)

    def __str__(self) -> str:
        lines = [
            f"objek            : {self.objects}",
            f"referensi        : {self.references}",
            f"dangling         : {len(self.dangling)}",
            f"rdf:ID duplikat  : {len(self.duplicate_ids)}",
        ]
        if self.degree:
            dist = collections.Counter(self.degree.values())
            total = len(self.degree)
            deg1 = dist.get(1, 0)
            lines.append(
                f"node berderajat-1: {deg1}/{total} = {100 * deg1 / total:.0f}%"
            )
        for cid in self.oversized:
            lines.append(
                f"  [!] node '{self.node_names.get(cid, cid)}' menampung "
                f"{self.degree[cid]} terminal -- melebihi batas {BUSBAR_DEGREE_LIMIT}; "
                "periksa apakah beberapa peralatan salah menunjuk node yang sama"
            )
        for cid in self.isolated[:5]:
            lines.append(
                f"  [i] node '{self.node_names.get(cid, cid)}' berderajat 1 "
                "(belum tersambung ke peralatan lain)"
            )
        if len(self.isolated) > 5:
            lines.append(f"  [i] ... dan {len(self.isolated) - 5} node berderajat-1 lainnya")
        return "\n".join(lines)


def check_topology(xml_path: str | Path) -> TopologyReport:
    s = Path(xml_path).read_text(encoding="utf-8")
    rep = TopologyReport()

    all_ids = re.findall(r'rdf:ID="_([^"]+)"', s)
    ids = set(all_ids)
    rep.objects = len(ids)
    seen = collections.Counter(all_ids)
    rep.duplicate_ids = [k for k, v in seen.items() if v > 1]

    refs = re.findall(r'rdf:resource="#_([^"]+)"', s)
    rep.references = len(refs)
    rep.dangling = sorted({r for r in refs if r not in ids})

    for m in re.finditer(
        r'<cim:ConnectivityNode rdf:ID="_([^"]+)">(.*?)</cim:ConnectivityNode>', s, re.S
    ):
        name = re.search(r"IdentifiedObject.name>([^<]*)", m.group(2))
        rep.node_names[m.group(1)] = name.group(1) if name else m.group(1)

    deg: collections.Counter = collections.Counter()
    for m in re.finditer(r"<cim:Terminal[^>]*>(.*?)</cim:Terminal>", s, re.S):
        cn = re.search(r'Terminal.ConnectivityNode rdf:resource="#_([^"]+)"', m.group(1))
        if cn:
            deg[cn.group(1)] += 1
    rep.degree = dict(deg)
    rep.isolated = sorted(k for k, v in deg.items() if v == 1)
    rep.oversized = sorted(k for k, v in deg.items() if v > BUSBAR_DEGREE_LIMIT)

    return rep

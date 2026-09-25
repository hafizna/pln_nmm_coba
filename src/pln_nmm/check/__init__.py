"""Validate generated CIM before it reaches a solver.

    topology.py  the graph: dangling refs, duplicate ids, degree-1 nodes,
                 and nodes that swallow a whole substation
    profile.py   the split: layout stays out of EQ, equipment stays out of DL,
                 and every diagram object points at real equipment

These run on emitted XML rather than in-memory objects, so they also catch
serialisation mistakes.
"""

from .profile import ProfileReport, check_profiles
from .topology import TopologyReport, check_topology

__all__ = [
    "ProfileReport",
    "TopologyReport",
    "check_profiles",
    "check_topology",
]

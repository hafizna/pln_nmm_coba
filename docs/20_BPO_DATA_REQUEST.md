# 20 — BPO Data Request for One-GI NMM Feasibility Pilot

Status: discussion/request draft.

## Request in one sentence

For the first NMM feasibility test, request **one representative GI** with:

1. a structurally cleaned asset extract scoped to that GI; and
2. the corresponding SLD GI with revision/source information.

This is intentionally much smaller than asking for a full UPT/ULTG/system
dataset.

## Why these two sources are required

The asset register answers:

> what physical assets exist, where they are registered, and what identity they
> carry.

The SLD answers:

> what electrical function those assets perform and how the primary network is
> connected.

Neither source alone is sufficient for an authoritative network model.

## A. Requested asset data

Preferred format: XLSX/CSV.

Minimum fields if available:

| Field | Need |
|---|---|
| ASSETNUM/source asset ID | required |
| SITEID/source site | required |
| GI identity/name | required |
| LOCATION/location ID | required |
| bay/location description | required |
| ASSETTYPE | required |
| GROUPTYPE | preferred |
| asset description | required |
| NIA | preferred |
| TECHIDENTNO | preferred |
| phase / R-S-T indication | preferred |
| manufacturer | optional for MVP |
| serial number | optional for MVP |
| install date/year | optional for MVP |
| active/status | preferred but not interpreted as switch state |
| source version/date | required |
| original/source row reference | preferred |

The request does **not** ask BPO to manually add:

- PMS Bus-I/Bus-II/Line role;
- terminal;
- ConnectivityNode;
- x/y;
- load-flow parameter;
- relay setting.

## B. Requested SLD

Preferred characteristics:

- full GI primary SLD;
- revision/date visible;
- approved/as-built status if available;
- readable bay/circuit names;
- readable PMT/PMS/ES/CT/PT-CVT/LA/trafo/line symbols;
- busbar arrangement visible;
- preferably original/vector source, but PDF/image is acceptable for the pilot.

If several revisions exist, provide the revision intended to correspond to the
asset extract or indicate the difference.

## C. Scope selection

Best pilot GI:

- asset data relatively complete;
- SLD available;
- has several bay types but is not exceptionally complex;
- data owner/reviewer can answer a small number of ambiguity questions.

A known Babel GI such as Kelapa may be used if the corresponding SLD can be
provided and BPO agrees on the pilot scope.

## D. Data not required yet

To keep the first request small, the pilot does **not** require:

- system-wide load flow;
- R/X/B for every line;
- transformer impedance;
- load P/Q;
- generator dispatch;
- SCADA real-time feed;
- relay/protection setting;
- defense-scheme logic;
- CGMES cross-border transaction package.

Those become later enrichment after topology feasibility is demonstrated.

## E. What BPO receives back

From the supplied GI package, the pilot will return:

- reconciled asset inventory;
- physical asset ↔ functional equipment map;
- per-bay review findings;
- explicit topology graph;
- generated SLD;
- CIM/XML;
- data-quality/conflict report;
- provenance trace;
- model readiness;
- measured manual-review burden.

## F. Why this is useful for the go/no-go decision

The pilot can answer quantitatively:

- how much of the model can be generated automatically;
- what information is absent from current upstream data;
- which ambiguities need engineering review;
- whether the maintenance burden is reasonable;
- whether NMM can realistically become an SSOT rather than another manually
  maintained database.

## G. Security / handling proposal

For the pilot:

- source remains inside PLN-approved handling environment;
- no public publishing of asset/topology data;
- source file is treated as immutable evidence;
- generated model records source/version provenance;
- review decisions are auditable;
- downstream export is controlled by scope/version.

Production authentication/RBAC is a later implementation item, but security
classification and data-owner approval should be agreed before scaling.

## H. Decision requested from BPO

1. Approve one GI as pilot scope.
2. Identify owner/contact for asset extract.
3. Identify owner/contact for the corresponding SLD.
4. Confirm whether the SLD is approved/as-built/current and its revision.
5. Confirm internal-use/security constraints for the prototype.
6. Nominate an engineering reviewer for a limited exception-review session.

The pilot does not ask BPO to commit to national rollout. It asks for enough real
evidence to determine whether that rollout is worth pursuing.

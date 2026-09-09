import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle


INPUT = "prism-uploads/all_quantum_issues_with_families.xlsx"
PNG_OUTPUT = "prism-uploads/rq3_all_families_heatmap_final_retained.png"
PDF_OUTPUT = "prism-uploads/rq3_all_families_heatmap_final_retained.pdf"

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def column_number(column):
    result = 0
    for character in column:
        result = result * 26 + ord(character) - 64
    return result


def read_first_sheet(path):
    with zipfile.ZipFile(path) as archive:
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared = [
            "".join(node.text or "" for node in item.iter(f"{{{NS['m']}}}t"))
            for item in shared_root.findall("m:si", NS)
        ]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships_root = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        relationships = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships_root
        }
        sheet = workbook.find("m:sheets/m:sheet", NS)
        target = relationships[sheet.attrib[f"{{{NS['r']}}}id"]]
        if not target.startswith("xl/"):
            target = "xl/" + target
        worksheet = ET.fromstring(archive.read(target))

        rows = []
        for row in worksheet.findall(".//m:sheetData/m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                column = re.match(r"[A-Z]+", cell.attrib["r"]).group()
                value_node = cell.find("m:v", NS)
                if value_node is None:
                    value = ""
                elif cell.attrib.get("t") == "s":
                    value = shared[int(value_node.text)]
                else:
                    value = value_node.text
                values[column] = value
            rows.append(values)

    columns = sorted(rows[0], key=column_number)
    headers = {column: rows[0][column] for column in columns}
    return [
        {headers[column]: row.get(column, "") for column in columns}
        for row in rows[1:]
    ]


records = read_first_sheet(INPUT)
retained = [
    record
    for record in records
    if record.get("Final_Status") == "Retained"
    and record.get("Include_in_Analysis") == "1"
]

repositories = [
    ("Qiskit/qiskit", "Qiskit"),
    ("pennylaneai/pennylane", "PennyLane"),
    ("quantumlib/cirq", "Cirq"),
    ("Quantinuum/tket", "TKET"),
    ("NVIDIA/cuda-quantum", "CUDA-Q"),
    ("amazon-braket/amazon-braket-sdk-python", "Amazon Braket\nSDK"),
    ("unitaryfoundation/mitiq", "Mitiq"),
    ("qutip/qutip", "QuTiP"),
    ("openqasm/openqasm", "OpenQASM"),
    ("rigetti/pyquil", "PyQuil"),
]
repository_keys = [item[0] for item in repositories]

family_repository_counts = defaultdict(Counter)
family_names = defaultdict(Counter)
repository_totals = Counter()
issue_label_counts = Counter()

for record in retained:
    ids = [item.strip() for item in record["Bug_Family_IDs"].split(",") if item.strip()]
    names = [
        item.strip() for item in record["Bug_Family_Names"].split(",") if item.strip()
    ]
    if len(ids) != len(names):
        raise ValueError(f"Family ID/name mismatch for issue {record['Issue Number']}")
    issue_label_counts[len(ids)] += 1
    repository = record["Organisation/Platform"]
    for family_id, family_name in zip(ids, names):
        family_repository_counts[family_id][repository] += 1
        family_names[family_id][family_name] += 1
        repository_totals[repository] += 1

family_ids = sorted(
    family_repository_counts,
    key=lambda family_id: ("FUN".index(family_id[0]), int(family_id[1:])),
)

name_overrides = {
    "N1": "JIT compatibility",
    "N2": "Numeric tolerance",
    "N3": "Postselection failure",
    "N4": "Native-language panic",
    "N5": "Test-infrastructure failure",
    "N6": "Index or bounds error",
    "N7": "Tracing error",
    "N8": "Recursion limit exceeded",
    "N9": "NaN calculation error",
    "N10": "Memory-management inefficiency",
    "N11": "Build-configuration error",
    "N12": "Parsing error",
    "N13": "Error-message mismatch",
    "N15": "Nondeterministic transpilation",
    "N16": "Silent configuration failure",
    "N17": "Unhandled native panic",
    "N18": "Visualization failure",
    "N19": "Symbolic-expression complexity",
    "N20": "Serialization failure",
    "N21": "In-place parameter mutation",
    "N22": "Mutator return-value inconsistency",
    "N23": "Batched-shape handling",
    "N24": "PyO3 thread-attachment error",
    "N25": "Inconsistent equality semantics",
    "N26": "Transform-program overwrite",
    "N27": "Invalid parameter handling",
    "N28": "Silent numerical truncation",
    "N29": "Mutable-reference leak",
    "N30": "Native memory corruption",
    "N31": "Invalid-state recovery",
    "N32": "Resource leak",
    "N33": "Assertion or unreachable-code panic",
    "N34": "Cache-invalidation error",
    "N35": "Inconsistent control-flow analysis",
    "N36": "Device-placement mismatch",
    "N37": "Compiler hang",
    "N38": "Instrumentation side effect",
    "N39": "Resource-lifecycle mismanagement",
    "N40": "Postselection-correlation failure",
    "N41": "State-persistence error",
    "N42": "Inconsistent bit-width handling",
    "N43": "Packaging error",
    "N44": "Type-annotation resolution failure",
    "N45": "Silent postselection failure",
    "N46": "GIL deadlock",
    "N47": "Transform-pipeline duplication",
    "N49": "Concurrency failure",
    "N50": "Mutable-state side effect",
    "N51": "Nondeterministic test",
    "N52": "Inconsistent protocol semantics",
    "N53": "Silent data loss",
    "N54": "Metadata-propagation error",
    "N55": "Symbol collision",
    "N56": "Unbounded resource consumption",
}


def display_name(family_id):
    if family_id in name_overrides:
        return name_overrides[family_id]
    return family_names[family_id].most_common(1)[0][0]


counts = np.array(
    [
        [family_repository_counts[family_id][repository] for repository in repository_keys]
        for family_id in family_ids
    ],
    dtype=int,
)
denominators = np.array([repository_totals[key] for key in repository_keys])
shares = counts / denominators[np.newaxis, :] * 100

family_totals = counts.sum(axis=1)
family_repository_totals = (counts > 0).sum(axis=1)
row_labels = [
    f"{family_id} — {display_name(family_id)} "
    f"(n={family_totals[index]}; "
    f"{family_repository_totals[index]} "
    f"{'repo' if family_repository_totals[index] == 1 else 'repos'})"
    for index, family_id in enumerate(family_ids)
]
column_labels = [
    f"{display}\n(n={repository_totals[key]})"
    for key, display in repositories
]

assert len(retained) == 356
assert issue_label_counts == Counter({1: 271, 2: 85})
assert counts.sum() == 441
assert len(family_ids) == 67
assert Counter(item[0] for item in family_ids) == Counter({"F": 4, "U": 9, "N": 54})
assert Counter(
    family_id[0] for row, family_id in enumerate(family_ids) for _ in range(family_totals[row])
) == Counter({"F": 5, "U": 77, "N": 359})
assert denominators.tolist() == [197, 133, 37, 27, 20, 12, 4, 6, 4, 1]

fig, ax = plt.subplots(figsize=(21, 25.5))
normalization = Normalize(vmin=0, vmax=100)
image = ax.imshow(shares, cmap="Blues", norm=normalization, aspect="auto")

ax.set_xticks(np.arange(len(column_labels)), labels=column_labels)
ax.set_yticks(np.arange(len(row_labels)), labels=row_labels)
ax.xaxis.tick_top()
ax.tick_params(axis="x", labelsize=8.5, pad=8, length=0)
ax.tick_params(axis="y", labelsize=7.5, pad=8, length=0)

for tick in ax.get_xticklabels():
    tick.set_fontweight("bold")

ax.set_xticks(np.arange(-0.5, counts.shape[1], 1), minor=True)
ax.set_yticks(np.arange(-0.5, counts.shape[0], 1), minor=True)
ax.grid(which="minor", color="#8d939b", linewidth=0.45)
ax.tick_params(which="minor", bottom=False, left=False)

for row in range(counts.shape[0]):
    for column in range(counts.shape[1]):
        value = counts[row, column]
        if value:
            color = "white" if shares[row, column] >= 45 else "#263442"
            ax.text(
                column,
                row,
                str(value),
                ha="center",
                va="center",
                fontsize=7.2,
                color=color,
                fontweight="medium",
            )

group_colors = {"F": "#0878b7", "U": "#f2ad00", "N": "#00a477"}
group_text = {
    "F": "F — Mutation-supported and curated: 4 families, 5 labels",
    "U": "U — Curated but mutation-unsupported: 9 families, 77 labels",
    "N": "N — Absent from both prior taxonomies: 54 families, 359 labels",
}

for group in "FUN":
    indices = [index for index, family_id in enumerate(family_ids) if family_id[0] == group]
    start, end = min(indices), max(indices)
    ax.add_patch(
        Rectangle(
            (-0.60, start - 0.5),
            0.10,
            end - start + 1,
            transform=ax.transData,
            facecolor=group_colors[group],
            edgecolor="none",
            clip_on=False,
        )
    )
    ax.text(
        -0.66,
        (start + end) / 2,
        group,
        rotation=90,
        ha="center",
        va="center",
        fontsize=10,
        color=group_colors[group],
        fontweight="bold",
        clip_on=False,
    )
    if start > 0:
        ax.axhline(start - 0.5, color="#353535", linewidth=1.35)

for spine in ax.spines.values():
    spine.set_color("#84909b")
    spine.set_linewidth(0.8)

fig.suptitle(
    "RQ3 Bug-Family Label Distribution Across Quantum Software Repositories",
    fontsize=17,
    fontweight="bold",
    color="#202b3a",
    y=0.986,
)
ax.set_title(
    "Cells show label counts; color indicates each count’s share of the repository total.",
    fontsize=10.5,
    fontweight="semibold",
    color="#36414c",
    pad=42,
)

colorbar = fig.colorbar(
    image,
    ax=ax,
    orientation="horizontal",
    fraction=0.018,
    pad=0.028,
    aspect=55,
    ticks=[0, 25, 50, 75, 100],
)
colorbar.set_label("Share of repository’s bug-family labels (%)", fontsize=9)
colorbar.ax.tick_params(labelsize=8)

fig.text(
    0.15,
    0.014,
    "   |   ".join(group_text[group] for group in "FUN"),
    ha="left",
    va="bottom",
    fontsize=8,
    color="#4c5663",
)

plt.subplots_adjust(left=0.29, right=0.985, top=0.922, bottom=0.075)
fig.savefig(PNG_OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(PDF_OUTPUT, bbox_inches="tight", facecolor="white")

print(f"Retained issues: {len(retained)}")
print(f"Single-label issues: {issue_label_counts[1]}")
print(f"Two-label issues: {issue_label_counts[2]}")
print(f"Labels: {counts.sum()}")
print(f"Families: {len(family_ids)}")
print("Family groups: F=4, U=9, N=54")
print("Label groups: F=5, U=77, N=359")
print("Repository totals:", denominators.tolist())
print(PNG_OUTPUT)
print(PDF_OUTPUT)
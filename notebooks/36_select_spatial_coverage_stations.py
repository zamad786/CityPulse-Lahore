import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lahore_multilocation_station_candidates.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lahore_spatial_selected_stations.csv"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "lahore_spatial_coverage_report.json"
)


# =========================================================
# COVERAGE SETTINGS
# =========================================================

COVERAGE_RADIUS_KM = 5.0

GRID_SPACING_KM = 0.5


# =========================================================
# PRESERVE CURRENT 8 STATIONS
# =========================================================

CURRENT_LOCATION_IDS = [
    4515157,  # Barki
    4527035,  # Civil Secretariat
    4527173,  # Learning Alliance DHA
    4555745,  # Ravi Road
    4568423,  # Model Town
    4609353,  # Kahna Hospital
    4618814,  # Gulberg III
    4757305,  # FCC University
]


# =========================================================
# HELPERS
# =========================================================

def latlon_to_xy_km(
    latitudes,
    longitudes,
    lat0,
    lon0,
):
    latitudes = np.asarray(
        latitudes,
        dtype=float,
    )

    longitudes = np.asarray(
        longitudes,
        dtype=float,
    )

    y = (
        latitudes
        - lat0
    ) * 111.32

    x = (
        longitudes
        - lon0
    ) * (
        111.32
        * math.cos(
            math.radians(
                lat0
            )
        )
    )

    return np.column_stack(
        [
            x,
            y,
        ]
    )


def convex_hull(
    points,
):
    """
    Andrew monotonic-chain convex hull.
    Returns hull vertices in order.
    """

    points = sorted(
        set(
            map(
                tuple,
                points,
            )
        )
    )

    if len(points) <= 1:
        return np.array(
            points,
            dtype=float,
        )

    def cross(
        origin,
        a,
        b,
    ):
        return (
            (
                a[0]
                - origin[0]
            )
            * (
                b[1]
                - origin[1]
            )
            -
            (
                a[1]
                - origin[1]
            )
            * (
                b[0]
                - origin[0]
            )
        )

    lower = []

    for point in points:
        while (
            len(lower) >= 2
            and cross(
                lower[-2],
                lower[-1],
                point,
            )
            <= 0
        ):
            lower.pop()

        lower.append(
            point
        )

    upper = []

    for point in reversed(
        points
    ):
        while (
            len(upper) >= 2
            and cross(
                upper[-2],
                upper[-1],
                point,
            )
            <= 0
        ):
            upper.pop()

        upper.append(
            point
        )

    hull = (
        lower[:-1]
        + upper[:-1]
    )

    return np.array(
        hull,
        dtype=float,
    )


def point_in_polygon(
    x,
    y,
    polygon,
):
    """
    Ray-casting point-in-polygon.
    """

    inside = False

    j = (
        len(polygon)
        - 1
    )

    for i in range(
        len(polygon)
    ):

        xi = polygon[i][0]
        yi = polygon[i][1]

        xj = polygon[j][0]
        yj = polygon[j][1]

        intersects = (
            (
                yi > y
            )
            != (
                yj > y
            )
        )

        if intersects:

            denominator = (
                yj - yi
            )

            if abs(
                denominator
            ) < 1e-12:
                denominator = 1e-12

            x_boundary = (
                (
                    xj - xi
                )
                * (
                    y - yi
                )
                / denominator
                + xi
            )

            if x < x_boundary:
                inside = (
                    not inside
                )

        j = i

    return inside


def polygon_area_km2(
    polygon,
):
    x = polygon[:, 0]
    y = polygon[:, 1]

    return 0.5 * abs(
        np.dot(
            x,
            np.roll(
                y,
                -1,
            ),
        )
        -
        np.dot(
            y,
            np.roll(
                x,
                -1,
            ),
        )
    )


# =========================================================
# LOAD CANDIDATES
# =========================================================

print()
print(
    "=============================================="
)
print(
    "CITYPULSE SPATIAL COVERAGE SELECTION"
)
print(
    "=============================================="
)


df = pd.read_csv(
    INPUT_PATH
)


usable = df[
    df[
        "usable_for_multilocation"
    ]
    == True
].copy()


usable = usable.reset_index(
    drop=True
)


print(
    f"All candidate rows: "
    f"{len(df)}"
)

print(
    f"Usable stations:    "
    f"{len(usable)}"
)


# =========================================================
# LOCAL KM COORDINATES
# =========================================================

lat0 = float(
    usable[
        "latitude"
    ].mean()
)

lon0 = float(
    usable[
        "longitude"
    ].mean()
)


station_xy = (
    latlon_to_xy_km(
        usable[
            "latitude"
        ],
        usable[
            "longitude"
        ],
        lat0,
        lon0,
    )
)


# =========================================================
# BUILD SERVICE-AREA HULL
# =========================================================

hull = convex_hull(
    station_xy
)


service_area_km2 = (
    polygon_area_km2(
        hull
    )
)


print(
    f"Usable-network hull area: "
    f"{service_area_km2:.2f} km²"
)


# =========================================================
# BUILD 0.5 KM GRID
# =========================================================

xmin = float(
    hull[:, 0].min()
)

xmax = float(
    hull[:, 0].max()
)

ymin = float(
    hull[:, 1].min()
)

ymax = float(
    hull[:, 1].max()
)


grid_points = []


x_values = np.arange(
    xmin,
    xmax
    + GRID_SPACING_KM,
    GRID_SPACING_KM,
)


y_values = np.arange(
    ymin,
    ymax
    + GRID_SPACING_KM,
    GRID_SPACING_KM,
)


for x in x_values:

    for y in y_values:

        if point_in_polygon(
            x,
            y,
            hull,
        ):
            grid_points.append(
                [
                    x,
                    y,
                ]
            )


grid = np.asarray(
    grid_points,
    dtype=float,
)


print(
    f"Coverage grid points: "
    f"{len(grid):,}"
)


# =========================================================
# DISTANCE MATRIX
# =========================================================

distance_matrix = np.sqrt(
    (
        (
            grid[:, None, :]
            - station_xy[
                None,
                :,
                :
            ]
        )
        ** 2
    ).sum(
        axis=2
    )
)


coverage_matrix = (
    distance_matrix
    <= COVERAGE_RADIUS_KM
)


# =========================================================
# START WITH CURRENT 8
# =========================================================

selected_indices = []


for location_id in (
    CURRENT_LOCATION_IDS
):

    matches = usable.index[
        usable[
            "location_id"
        ].astype(int)
        == int(
            location_id
        )
    ].tolist()

    if not matches:
        raise ValueError(
            f"Current station "
            f"{location_id} "
            "is not usable."
        )

    selected_indices.append(
        matches[0]
    )


uncovered = ~(
    coverage_matrix[
        :,
        selected_indices
    ]
    .any(
        axis=1
    )
)


initial_coverage = (
    1.0
    - uncovered.mean()
)


print()
print(
    "CURRENT 8-STATION COVERAGE"
)

print(
    f"Within 5 km: "
    f"{initial_coverage * 100:.2f}%"
)


# =========================================================
# GREEDY ADDITION
#
# Add the usable station that covers the
# largest number of currently uncovered
# grid points.
#
# Tie-break:
# 1. score
# 2. recent coverage
# 3. history days
# =========================================================

while True:

    gains = (
        coverage_matrix[
            uncovered
        ]
        .sum(
            axis=0
        )
    )


    for index in (
        selected_indices
    ):
        gains[index] = 0


    best_gain = int(
        gains.max()
    )


    if best_gain <= 0:
        break


    candidates = np.where(
        gains
        == best_gain
    )[0]


    best_index = max(
        candidates,
        key=lambda index: (
            int(
                usable.loc[
                    index,
                    "score"
                ]
            ),

            float(
                usable.loc[
                    index,
                    "recent_coverage_pct"
                ]
            ),

            float(
                usable.loc[
                    index,
                    "history_days"
                ]
            ),
        ),
    )


    selected_indices.append(
        int(
            best_index
        )
    )


    uncovered = (
        uncovered
        & ~coverage_matrix[
            :,
            best_index
        ]
    )


    coverage_pct = (
        100
        * (
            1.0
            - uncovered.mean()
        )
    )


    station_name = (
        usable.loc[
            best_index,
            "location_name"
        ]
    )


    print(
        f"Added #{len(selected_indices)}: "
        f"{station_name}"
    )

    print(
        f"  5 km coverage: "
        f"{coverage_pct:.2f}%"
    )


# =========================================================
# FINAL METRICS
# =========================================================

selected_distance = (
    distance_matrix[
        :,
        selected_indices
    ]
    .min(
        axis=1
    )
)


final_coverage_pct = (
    100
    * (
        selected_distance
        <= COVERAGE_RADIUS_KM
    ).mean()
)


maximum_distance_km = float(
    selected_distance.max()
)


p95_distance_km = float(
    np.percentile(
        selected_distance,
        95,
    )
)


selected = (
    usable
    .iloc[
        selected_indices
    ]
    .copy()
)


selected[
    "selection_order"
] = np.arange(
    1,
    len(selected)
    + 1,
)


selected[
    "coverage_radius_km"
] = (
    COVERAGE_RADIUS_KM
)


selected.to_csv(
    OUTPUT_PATH,
    index=False,
)


# =========================================================
# REPORT
# =========================================================

report = {
    "usable_candidate_count":
        int(
            len(
                usable
            )
        ),

    "preserved_current_station_count":
        len(
            CURRENT_LOCATION_IDS
        ),

    "selected_station_count":
        int(
            len(
                selected
            )
        ),

    "coverage_radius_km":
        COVERAGE_RADIUS_KM,

    "grid_spacing_km":
        GRID_SPACING_KM,

    "service_area_definition":
        (
            "Convex hull of usable "
            "OpenAQ station coordinates"
        ),

    "service_area_km2":
        float(
            service_area_km2
        ),

    "initial_8_coverage_pct":
        float(
            initial_coverage
            * 100
        ),

    "final_coverage_pct":
        float(
            final_coverage_pct
        ),

    "maximum_nearest_station_distance_km":
        maximum_distance_km,

    "p95_nearest_station_distance_km":
        p95_distance_km,

    "selected_location_ids":
        selected[
            "location_id"
        ].astype(
            int
        ).tolist(),

    "selected_locations":
        selected[
            [
                "location_id",
                "location_name",
                "sensor_id",
                "latitude",
                "longitude",
                "provider",
                "recent_coverage_pct",
                "history_days",
                "score",
            ]
        ].to_dict(
            orient="records"
        ),

    "important_note":
        (
            "Coverage statistics describe the "
            "convex service area represented by "
            "usable OpenAQ stations. They do not "
            "represent the official administrative "
            "boundary of Lahore."
        ),
}


REPORT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)


REPORT_PATH.write_text(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# =========================================================
# OUTPUT
# =========================================================

print()
print(
    "=============================================="
)
print(
    "FINAL SPATIAL SELECTION"
)
print(
    "=============================================="
)


print(
    selected[
        [
            "selection_order",
            "location_id",
            "location_name",
            "provider",
            "recent_coverage_pct",
        ]
    ].to_string(
        index=False
    )
)


print()
print(
    f"Selected stations: "
    f"{len(selected)}"
)

print(
    f"5 km coverage: "
    f"{final_coverage_pct:.2f}%"
)

print(
    f"95th percentile distance: "
    f"{p95_distance_km:.2f} km"
)

print(
    f"Maximum distance: "
    f"{maximum_distance_km:.2f} km"
)

print()
print(
    f"CSV:    "
    f"{OUTPUT_PATH}"
)

print(
    f"Report: "
    f"{REPORT_PATH}"
)

print()
print(
    "SPATIAL COVERAGE SELECTION: PASS"
)

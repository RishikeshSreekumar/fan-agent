"""Read-only company reference, transcribed from the supplied image."""

import math


def cmm_to_cfm(value):
    return value / (0.3048 ** 3)


def shaft_power(torque_nm, rpm):
    return torque_nm * rpm * 2 * math.pi / 60


def reference():
    velocities = [2.98545, 3.08606, 3.30608, 3.20141, 2.87071, 2.66466,
                  1.97076, 1.31737, 0.869433, 0.590596, 0.414618, 0.324237]
    return {
        "id": "company-inveno-ul-itr4", "name": "Inveno UL · ITR4",
        "kind": "company_reference", "solver": "Ansys 2024 R1",
        "date_as_shown": "06-07-2026", "rpm": 280,
        "air_delivery_cmm": 232.65, "air_delivery_cfm": cmm_to_cfm(232.65),
        "torque_nm": 0.76, "shaft_power_w": shaft_power(0.76, 280),
        "runtime_hours": 13.5, "cores": 32,
        "samples": [{"position_mm": 40 + i * 80, "velocity_ms": v} for i, v in enumerate(velocities)],
        "provenance": "Manually transcribed from the user-supplied company report image. Not generated or independently verified by Fan-Agent.",
        "series_label_as_shown": "Inveno_5B",
        "position_label_as_shown": "STL Location",
        "unknowns": [
            "Meaning and origin of STL Location; radial direction is not assumed.",
            "Sampling plane height, velocity component and averaging method.",
            "Air-delivery integration area, sign convention and calculation method.",
            "CAD, room dimensions, mounting height and rotation direction.",
            "Mesh, turbulence model, wall treatment and convergence criteria.",
            "The table label says Inveno_5B while the geometry illustration appears to show three blades; blade count is unconfirmed."
        ],
        "notes": [
            "CMM is cubic metres per minute. CFM is converted from the reported CMM.",
            "Shaft power is calculated from the reported torque and speed; electrical power is unknown.",
            "The displayed velocity curve is not used to reconstruct or validate the reported air delivery."
        ]
    }

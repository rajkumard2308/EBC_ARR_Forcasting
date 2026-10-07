from datetime import date, timedelta

import streamlit as st

from services.ipms import (
    calculate_night_metrics,
    fetch_date_range,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EBC Revenue & ADR Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL CSS
# ============================================================

st.html(
    """
<style>

html,
body {
    background: #080c14 !important;
}

.stApp {
    background:
        radial-gradient(
            circle at 15% 0%,
            #172033 0%,
            #0b101b 35%,
            #070a11 100%
        );

    color: #e5e7eb;
}


/* ============================================================
   MAIN
   ============================================================ */

.block-container {
    max-width: 1500px;

    padding-top: 4.2rem;
    padding-bottom: 4rem;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #111622 0%,
            #0d111b 100%
        );

    border-right: 1px solid #222b3d;
}

section[data-testid="stSidebar"]
.block-container {
    padding-top: 2rem;
}


/* ============================================================
   HEADER
   ============================================================ */

.dashboard-header {
    display: flex;

    align-items: center;

    gap: 14px;

    margin-bottom: 4px;
}

.dashboard-icon {
    font-size: 40px;

    line-height: 1;
}

.dashboard-title {
    color: #f8fafc;

    font-size: 34px;

    font-weight: 850;

    letter-spacing: -1px;

    line-height: 1.15;
}

.dashboard-subtitle {
    color: #8492aa;

    font-size: 13px;

    margin-left: 55px;

    margin-top: 5px;

    margin-bottom: 30px;
}


/* ============================================================
   SECTION TITLE
   ============================================================ */

.section-title {
    color: #f8fafc;

    font-size: 24px;

    font-weight: 800;

    letter-spacing: -0.4px;

    margin-top: 30px;

    margin-bottom: 15px;
}


/* ============================================================
   METRIC CARDS
   ============================================================ */

.metric-card {
    background:
        linear-gradient(
            145deg,
            #182135 0%,
            #101622 100%
        );

    border: 1px solid #29354c;

    border-radius: 16px;

    padding: 20px;

    min-height: 132px;

    box-sizing: border-box;

    box-shadow:
        0 14px 35px rgba(
            0,
            0,
            0,
            0.24
        );

    transition:
        transform 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-3px);

    border-color: #40516f;

    box-shadow:
        0 18px 45px rgba(
            0,
            0,
            0,
            0.34
        );
}

.metric-top {
    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 10px;
}

.metric-label {
    color: #8fa0ba;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 0.65px;

    text-transform: uppercase;

    line-height: 1.35;
}

.metric-icon {
    color: #67e8f9;

    font-size: 16px;

    font-weight: 800;

    flex-shrink: 0;
}

.metric-value {
    color: #f8fafc;

    font-size: 27px;

    font-weight: 850;

    margin-top: 16px;

    line-height: 1.1;
}

.metric-sub {
    color: #63718a;

    font-size: 11px;

    margin-top: 8px;

    line-height: 1.4;
}


/* ============================================================
   INFO BOX
   ============================================================ */

.info-box {
    background:
        linear-gradient(
            135deg,
            #111a29,
            #0d1420
        );

    border: 1px solid #29354a;

    border-radius: 13px;

    padding: 16px 18px;

    color: #91a2bc;

    font-size: 12px;

    line-height: 1.7;

    margin-top: 15px;
}

.info-box strong {
    color: #dbeafe;
}


/* ============================================================
   NIGHT CALL
   ============================================================ */

.night-call {
    background:
        linear-gradient(
            135deg,
            #151d2c,
            #101723
        );

    border: 1px solid #263149;

    border-radius: 9px;

    padding: 10px 12px;

    color: #a5b4fc;

    font-family: monospace;

    font-size: 11px;

    margin-bottom: 8px;
}


/* ============================================================
   DAILY CHART
   ============================================================ */

.daily-chart {
    background:
        linear-gradient(
            145deg,
            #111824,
            #0c111b
        );

    border: 1px solid #242e42;

    border-radius: 15px;

    padding: 20px;

    margin-top: 10px;

    overflow-x: auto;
}

.chart-header {
    display: grid;

    grid-template-columns:
        110px
        1fr
        110px;

    gap: 15px;

    color: #65738c;

    font-size: 9px;

    font-weight: 850;

    letter-spacing: 0.8px;

    margin-bottom: 18px;
}

.chart-row {
    display: grid;

    grid-template-columns:
        110px
        1fr
        110px;

    gap: 15px;

    align-items: center;

    margin-bottom: 13px;
}

.chart-date {
    color: #cbd5e1;

    font-size: 12px;

    font-weight: 650;
}

.chart-track {
    height: 12px;

    background: #1b2536;

    border-radius: 99px;

    overflow: hidden;
}

.chart-bar {
    height: 100%;

    background:
        linear-gradient(
            90deg,
            #38bdf8,
            #818cf8
        );

    border-radius: 99px;

    transition: width 0.7s ease;
}

.chart-value {
    color: #f8fafc;

    font-size: 12px;

    font-weight: 800;

    text-align: right;
}


/* ============================================================
   DAILY TABLE
   ============================================================ */

.daily-table-wrapper {
    background: #0d121b;

    border: 1px solid #252f42;

    border-radius: 14px;

    overflow-x: auto;

    margin-top: 14px;
}

.daily-table {
    width: 100%;

    min-width: 800px;

    border-collapse: collapse;
}

.daily-table th {
    background: #171e2c;

    color: #7e8da6;

    font-size: 10px;

    font-weight: 850;

    letter-spacing: 0.7px;

    padding: 14px 15px;

    text-align: left;
}

.daily-table td {
    color: #d9e2ef;

    font-size: 12px;

    padding: 14px 15px;

    border-top: 1px solid #202939;
}

.daily-table tbody tr:hover {
    background: #151c29;
}

.green {
    color: #4ade80 !important;

    font-weight: 850;
}

.gray {
    color: #94a3b8 !important;

    font-weight: 700;
}

.blue {
    color: #67e8f9 !important;

    font-weight: 850;
}


/* ============================================================
   ROOM TABLE
   ============================================================ */

.room-table-wrapper {
    background: #0d121b;

    border: 1px solid #252f42;

    border-radius: 14px;

    overflow-x: auto;
}

.room-table {
    width: 100%;

    min-width: 1000px;

    border-collapse: collapse;
}

.room-table th {
    background: #171e2c;

    color: #7e8da6;

    font-size: 10px;

    font-weight: 850;

    letter-spacing: 0.6px;

    padding: 14px 12px;

    text-align: left;
}

.room-table td {
    color: #d9e2ef;

    font-size: 12px;

    padding: 13px 12px;

    border-top: 1px solid #202939;
}

.room-table tbody tr:hover {
    background: #151c29;
}

.room-name {
    color: #f1f5f9;

    font-weight: 750;
}

.available {
    color: #4ade80;

    font-weight: 850;
}

.zero {
    color: #64748b;

    font-weight: 700;
}

.price {
    color: #e2e8f0;

    font-weight: 650;
}

.per-room {
    color: #67e8f9;

    font-weight: 800;
}

.revenue {
    color: #c4b5fd;

    font-weight: 750;
}


/* ============================================================
   NIGHT SUMMARY
   ============================================================ */

.night-summary {
    background:
        linear-gradient(
            135deg,
            #111a29,
            #0d1420
        );

    border: 1px solid #2a354b;

    border-radius: 12px;

    padding: 15px 17px;

    margin-top: 12px;

    color: #a6b4c8;

    font-size: 12px;

    line-height: 1.8;
}

.night-summary strong {
    color: #f8fafc;
}


/* ============================================================
   FOOTER
   ============================================================ */

.footer {
    text-align: center;

    color: #536178;

    font-size: 11px;

    margin-top: 45px;

    padding-bottom: 20px;
}


/* ============================================================
   STREAMLIT CLEANUP
   ============================================================ */

div[data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

</style>
"""
)


# ============================================================
# HELPERS
# ============================================================

def money(value: float) -> str:
    return f"₹{value:,.0f}"


def money_decimal(value: float) -> str:
    return f"₹{value:,.2f}"


def format_date(value: date) -> str:
    return value.strftime("%d-%m-%Y")


def make_night_ranges(
    from_date: date,
    to_date: date,
):
    ranges = []

    current = from_date

    while current < to_date:

        next_date = (
            current
            + timedelta(days=1)
        )

        ranges.append(
            (current, next_date)
        )

        current = next_date

    return ranges


# ============================================================
# METRIC CARD
# ============================================================

def render_metric(
    label: str,
    value: str,
    subtitle: str,
    icon: str,
):

    html = f"""
<div class="metric-card">

    <div class="metric-top">

        <span class="metric-label">
            {label}
        </span>

        <span class="metric-icon">
            {icon}
        </span>

    </div>

    <div class="metric-value">
        {value}
    </div>

    <div class="metric-sub">
        {subtitle}
    </div>

</div>
"""

    st.html(html)


# ============================================================
# DAILY ADR CHART
# ============================================================

def render_daily_chart(
    daily_metrics: list[dict],
):

    if not daily_metrics:
        return

    max_adr = max(
        (
            item["adr"]
            for item in daily_metrics
        ),
        default=0,
    )

    if max_adr <= 0:
        max_adr = 1

    rows = []

    for item in daily_metrics:

        width = (
            item["adr"]
            / max_adr
            * 100
        )

        rows.append(
            f"""
<div class="chart-row">

    <div class="chart-date">
        {format_date(item["date"])}
    </div>

    <div class="chart-track">

        <div
            class="chart-bar"
            style="width:{width:.2f}%"
        ></div>

    </div>

    <div class="chart-value">
        {money(item["adr"])}
    </div>

</div>
"""
        )

    html = f"""
<div class="daily-chart">

    <div class="chart-header">

        <span>DATE</span>

        <span>ADR</span>

        <span>VALUE</span>

    </div>

    {''.join(rows)}

</div>
"""

    st.html(html)


# ============================================================
# DAILY PERFORMANCE TABLE
# ============================================================

def render_daily_table(
    daily_metrics: list[dict],
):

    rows = []

    for item in daily_metrics:

        rows.append(
            f"""
<tr>

    <td>
        {format_date(item["date"])}
    </td>

    <td class="green">
        {item["available_physical_rooms"]}
    </td>

    <td class="gray">
        {item["unavailable_physical_rooms"]}
    </td>

    <td>
        {item["availability_percent"]:.1f}%
    </td>

    <td>
        {money(item["available_revenue"])}
    </td>

    <td class="blue">
        {money(item["adr"])}
    </td>

</tr>
"""
        )

    html = f"""
<div class="daily-table-wrapper">

<table class="daily-table">

<thead>

<tr>

    <th>DATE</th>

    <th>AVAILABLE</th>

    <th>UNAVAILABLE</th>

    <th>AVAILABILITY</th>

    <th>FORECAST REVENUE</th>

    <th>ADR</th>

</tr>

</thead>

<tbody>

{''.join(rows)}

</tbody>

</table>

</div>
"""

    st.html(html)


# ============================================================
# ROOM TABLE
# ============================================================

def render_room_table(
    rooms: list[dict],
):

    rows = []

    for room in rooms:

        physical_left = room[
            "physical_rooms_left"
        ]

        availability_class = (
            "available"
            if physical_left > 0
            else "zero"
        )

        rows.append(
            f"""
<tr>

    <td class="room-name">
        {room["room_type"]}
    </td>

    <td class="price">
        {money_decimal(
            room["price_per_ipms_unit"]
        )}
    </td>

    <td>
        {room["ipms_units_left"]}
    </td>

    <td>
        {room["rooms_per_unit"]}
    </td>

    <td class="{availability_class}">
        {physical_left}
    </td>

    <td class="per-room">
        {money_decimal(
            room["per_room_price"]
        )}
    </td>

    <td class="revenue">
        {money_decimal(
            room["available_room_revenue"]
        )}
    </td>

</tr>
"""
        )

    html = f"""
<div class="room-table-wrapper">

<table class="room-table">

<thead>

<tr>

    <th>ROOM TYPE</th>

    <th>PRICE / IPMS UNIT</th>

    <th>IPMS UNITS LEFT</th>

    <th>ROOMS / UNIT</th>

    <th>PHYSICAL ROOMS LEFT</th>

    <th>PER PHYSICAL ROOM</th>

    <th>AVAILABLE REVENUE</th>

</tr>

</thead>

<tbody>

{''.join(rows)}

</tbody>

</table>

</div>
"""

    st.html(html)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 📅 Date Range"
    )

    from_date = st.date_input(
        "From date",
        value=date.today(),
        format="DD-MM-YYYY",
    )

    to_date = st.date_input(
        "To date",
        value=(
            date.today()
            + timedelta(days=1)
        ),
        format="DD-MM-YYYY",
    )

    st.divider()

    if to_date > from_date:

        st.markdown(
            """
            **The selected range is split into
            individual hotel nights.**
            """
        )

        st.markdown(
            "#### Nightly API calls"
        )

        for start, end in make_night_ranges(
            from_date,
            to_date,
        ):

            st.html(
                f"""
<div class="night-call">
    {format_date(start)}
    →
    {format_date(end)}
</div>
"""
            )

    else:

        st.error(
            "To date must be after From date."
        )

    st.divider()

    fetch_button = st.button(
        "🔄 Fetch latest IPMS data",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# HEADER
# ============================================================

st.html(
    """
<div class="dashboard-header">

    <div class="dashboard-icon">
        🏨
    </div>

    <div class="dashboard-title">
        EBC Revenue &amp; ADR Dashboard
    </div>

</div>

<div class="dashboard-subtitle">
    Everest Base Camp • Mussoorie • IPMS RoomList Forecast
</div>
"""
)


# ============================================================
# DATE VALIDATION
# ============================================================

if to_date <= from_date:

    st.error(
        "Please select a To date after the From date."
    )

    st.stop()


# ============================================================
# FETCH CONTROL
# ============================================================

selected_range = (
    from_date,
    to_date,
)

need_fetch = (
    "nightly_data"
    not in st.session_state
)

range_changed = (
    st.session_state.get(
        "selected_range"
    )
    != selected_range
)


if (
    fetch_button
    or need_fetch
    or range_changed
):

    with st.spinner(
        "Fetching IPMS RoomList data..."
    ):

        try:

            nightly_data = fetch_date_range(
                from_date=from_date,
                to_date=to_date,
            )

            st.session_state[
                "nightly_data"
            ] = nightly_data

            st.session_state[
                "selected_range"
            ] = selected_range

        except Exception as exc:

            st.error(
                "Unable to fetch IPMS data."
            )

            st.exception(exc)

            st.stop()


nightly_data = st.session_state[
    "nightly_data"
]


# ============================================================
# DAILY METRICS
# ============================================================

daily_metrics = []

for night in nightly_data:

    metrics = calculate_night_metrics(
        night
    )

    daily_metrics.append(
        metrics
    )


# ============================================================
# RANGE TOTALS
# ============================================================

total_available_room_nights = sum(
    item[
        "available_physical_rooms"
    ]
    for item in daily_metrics
)

total_unavailable_room_nights = sum(
    item[
        "unavailable_physical_rooms"
    ]
    for item in daily_metrics
)

total_forecast_revenue = sum(
    item[
        "available_revenue"
    ]
    for item in daily_metrics
)

total_inventory_room_nights = sum(
    item[
        "total_physical_inventory"
    ]
    for item in daily_metrics
)


if total_available_room_nights > 0:

    range_adr = (
        total_forecast_revenue
        / total_available_room_nights
    )

else:

    range_adr = 0.0


if total_inventory_room_nights > 0:

    range_availability = (
        total_available_room_nights
        / total_inventory_room_nights
        * 100
    )

else:

    range_availability = 0.0


# ============================================================
# FORECAST SUMMARY
# ============================================================

st.html(
    """
<div class="section-title">
    📊 Forecast Summary
</div>
"""
)

metric_columns = st.columns(5)

with metric_columns[0]:

    render_metric(
        "FORECAST AVAILABLE REVENUE",
        money(
            total_forecast_revenue
        ),
        "Current IPMS available rooms",
        "₹",
    )


with metric_columns[1]:

    render_metric(
        "AVAILABLE ROOM NIGHTS",
        str(
            total_available_room_nights
        ),
        "Physical rooms available",
        "🛏",
    )


with metric_columns[2]:

    render_metric(
        "UNAVAILABLE ROOM NIGHTS",
        str(
            total_unavailable_room_nights
        ),
        "Not currently sellable",
        "◌",
    )


with metric_columns[3]:

    render_metric(
        "AVAILABILITY",
        f"{range_availability:.1f}%",
        "Against 14 physical rooms",
        "%",
    )


with metric_columns[4]:

    render_metric(
        "ADR",
        money(
            range_adr
        ),
        "Available-room weighted ADR",
        "↗",
    )


# ============================================================
# INFORMATION
# ============================================================

st.html(
    f"""
<div class="info-box">

<strong>IPMS RoomList:</strong>
{len(nightly_data)} night(s) fetched separately.

&nbsp; • &nbsp;

<strong>Physical inventory:</strong>
14 rooms.

&nbsp; • &nbsp;

<strong>Twin:</strong>
1 IPMS unit = 2 physical rooms.

&nbsp; • &nbsp;

<strong>Villa:</strong>
1 IPMS unit = 2 physical rooms.

&nbsp; • &nbsp;

<strong>Unavailable ≠ Sold:</strong>
RoomList availability does not prove that a room
was actually booked.

</div>
"""
)


# ============================================================
# DAILY ADR
# ============================================================

st.html(
    """
<div class="section-title">
    📈 Daily ADR
</div>
"""
)

render_daily_chart(
    daily_metrics
)


# ============================================================
# DAILY PERFORMANCE
# ============================================================

st.html(
    """
<div class="section-title">
    📅 Daily Performance
</div>
"""
)

render_daily_table(
    daily_metrics
)


# ============================================================
# ROOM-WISE DAILY DATA
# ============================================================

st.html(
    """
<div class="section-title">
    🛏️ Room-wise Daily IPMS Data
</div>
"""
)


for night, metrics in zip(
    nightly_data,
    daily_metrics,
):

    st.markdown(
        f"""
### {format_date(
    night["check_in"]
)}
→
{format_date(
    night["check_out"]
)}
"""
    )

    render_room_table(
        night["rooms"]
    )

    st.html(
        f"""
<div class="night-summary">

<strong>Night ADR:</strong>
{money_decimal(
    metrics["adr"]
)}

&nbsp; | &nbsp;

<strong>Available:</strong>
{metrics[
    "available_physical_rooms"
]}
/
{metrics[
    "total_physical_inventory"
]}
physical rooms

&nbsp; | &nbsp;

<strong>Unavailable:</strong>
{metrics[
    "unavailable_physical_rooms"
]}

&nbsp; | &nbsp;

<strong>Availability:</strong>
{metrics[
    "availability_percent"
]:.1f}%

&nbsp; | &nbsp;

<strong>Forecast available revenue:</strong>
{money_decimal(
    metrics["available_revenue"]
)}

</div>
"""
    )


# ============================================================
# CALCULATION LOGIC
# ============================================================

st.html(
    """
<div class="section-title">
    ⚙️ Calculation Logic
</div>
"""
)

st.html(
    """
<div class="info-box">

<ul>

<li>
Selected date range is split into individual
one-night IPMS RoomList calls.
</li>

<li>
Example:
<strong>12-Oct → 14-Oct</strong>
becomes
<strong>12-Oct → 13-Oct</strong>
and
<strong>13-Oct → 14-Oct</strong>.
</li>

<li>
IPMS <strong>available_rooms</strong> represents
sellable IPMS units.
</li>

<li>
<strong>Glamper:</strong>
1 IPMS unit = 1 physical room.
</li>

<li>
<strong>Surveyor:</strong>
1 IPMS unit = 1 physical room.
</li>

<li>
<strong>Twin Luxury Cottage:</strong>
1 IPMS unit = 2 physical rooms.
</li>

<li>
<strong>Andrew's Villa:</strong>
1 IPMS unit = 2 physical rooms.
</li>

<li>
Physical availability =
<strong>
IPMS units × rooms per unit
</strong>.
</li>

<li>
Forecast available revenue =
<strong>
physical rooms available × per-room price
</strong>.
</li>

<li>
ADR =
<strong>
available revenue ÷ available physical rooms
</strong>.
</li>

<li>
Unavailable rooms are not treated as sold rooms.
Actual sold rooms require reservation data.
</li>

</ul>

</div>
"""
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
<div class="footer">
    EBC Revenue &amp; ADR Dashboard
    •
    IPMS RoomList Forecast
</div>
"""
)
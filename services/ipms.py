import os
import re
from datetime import date, timedelta
from typing import Any

import requests
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

HOTEL_CODE = os.getenv("IPMS_HOTEL_CODE", "23400")
OPENAPI_KEY = os.getenv("IPMS_OPENAPI_KEY")

API_URL = (
    "https://live.ipms247.com/"
    "booking/reservation_api/listing.php"
)


# ============================================================
# EBC PHYSICAL ROOM CONFIGURATION
#
# IMPORTANT:
# This is NOT daily availability.
#
# This only tells the dashboard how many physical rooms
# are represented by one IPMS sellable unit.
# ============================================================

ROOM_CONFIG = {
    "Camper": {
        "physical_inventory": 1,
        "rooms_per_ipms_unit": 1,
    },

    "Glamper": {
        "physical_inventory": 4,
        "rooms_per_ipms_unit": 1,
    },

    "Surveyor": {
        "physical_inventory": 1,
        "rooms_per_ipms_unit": 1,
    },

    "Surveyor Suite": {
        "physical_inventory": 1,
        "rooms_per_ipms_unit": 1,
    },

    "Zenith Luxury Cottage": {
        "physical_inventory": 1,
        "rooms_per_ipms_unit": 1,
    },

    "Twin Luxury Cottages": {
        "physical_inventory": 2,
        "rooms_per_ipms_unit": 2,
    },

    "Andrew's Villa": {
        "physical_inventory": 4,
        "rooms_per_ipms_unit": 2,
    },
}


ROOM_ORDER = [
    "Camper",
    "Glamper",
    "Surveyor",
    "Surveyor Suite",
    "Zenith Luxury Cottage",
    "Twin Luxury Cottages",
    "Andrew's Villa",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_name(value: Any) -> str:
    """
    Normalize IPMS room names.

    Handles:
    - Andrew's Villa
    - Andrew’s Villa
    - different spacing
    - different capitalization
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = (
        text
        .replace("’", "'")
        .replace("`", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    text = re.sub(r"\s+", " ", text)

    return text


def canonical_room_type(record: dict) -> str | None:
    """
    Convert whatever IPMS calls the room into our EBC
    canonical room name.

    We intentionally use keyword matching instead of depending
    on one exact Room_Name / Roomtype_Name value.
    """

    candidates = [
        record.get("Roomtype_Short_code"),
        record.get("Roomtype_Name"),
        record.get("Room_Name"),
    ]

    normalized_values = [
        normalize_name(value)
        for value in candidates
        if value
    ]

    combined = " | ".join(normalized_values)

    # Order matters:
    # "Surveyor Suite" must be detected before "Surveyor".
    if "surveyor suite" in combined:
        return "Surveyor Suite"

    if "zenith" in combined:
        return "Zenith Luxury Cottage"

    if "twin" in combined:
        return "Twin Luxury Cottages"

    if "villa" in combined:
        return "Andrew's Villa"

    if "glamper" in combined:
        return "Glamper"

    if "camper" in combined:
        return "Camper"

    if "surveyor" in combined:
        return "Surveyor"

    return None


# ============================================================
# TYPE CONVERSION
# ============================================================

def to_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        if value is None or value == "":
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


def to_int(
    value: Any,
    default: int = 0,
) -> int:

    try:

        if value is None or value == "":
            return default

        return int(float(value))

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# RESPONSE PARSING
# ============================================================

def extract_room_records(
    payload: Any,
) -> list[dict]:

    if isinstance(payload, list):

        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    if not isinstance(payload, dict):

        return []

    possible_keys = [
        "RoomList",
        "roomList",
        "rooms",
        "Rooms",
        "data",
        "Data",
        "result",
        "Result",
    ]

    for key in possible_keys:

        value = payload.get(key)

        if isinstance(value, list):

            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

        if isinstance(value, dict):

            nested = extract_room_records(value)

            if nested:
                return nested

    # Some APIs return a single room object.
    if (
        "Room_Name" in payload
        or "Roomtype_Name" in payload
        or "Roomtype_Short_code" in payload
    ):

        return [payload]

    return []


# ============================================================
# DATE-SPECIFIC AVAILABILITY
# ============================================================

def get_available_units(
    record: dict,
    target_date: date,
) -> int:

    availability = (
        record.get("available_rooms")
        or {}
    )

    if not isinstance(
        availability,
        dict,
    ):

        return 0

    date_key = target_date.isoformat()

    return max(
        to_int(
            availability.get(
                date_key
            ),
            0,
        ),
        0,
    )


# ============================================================
# DATE-SPECIFIC PRICE
# ============================================================

def get_price(
    record: dict,
    target_date: date,
) -> float:

    rate_info = (
        record.get("room_rates_info")
        or {}
    )

    date_key = target_date.isoformat()

    # --------------------------------------------------------
    # Preferred:
    # exclusive_tax
    #
    # This is the room rate before tax.
    # --------------------------------------------------------

    exclusive_tax = (
        rate_info.get(
            "exclusive_tax"
        )
        or {}
    )

    if isinstance(
        exclusive_tax,
        dict,
    ):

        value = exclusive_tax.get(
            date_key
        )

        if value not in (
            None,
            "",
        ):

            price = to_float(
                value
            )

            if price > 0:
                return price

    # --------------------------------------------------------
    # Fallback:
    # avg_per_night_without_tax
    # --------------------------------------------------------

    value = rate_info.get(
        "avg_per_night_without_tax"
    )

    price = to_float(
        value
    )

    if price > 0:
        return price

    # --------------------------------------------------------
    # Additional fallback:
    # avg_per_night_after_discount
    # --------------------------------------------------------

    value = rate_info.get(
        "avg_per_night_after_discount"
    )

    return max(
        to_float(value),
        0,
    )


# ============================================================
# TAX
# ============================================================

def get_tax(
    record: dict,
    target_date: date,
) -> float:

    rate_info = (
        record.get("room_rates_info")
        or {}
    )

    tax = (
        rate_info.get("tax")
        or {}
    )

    if not isinstance(
        tax,
        dict,
    ):

        return 0.0

    return to_float(
        tax.get(
            target_date.isoformat()
        )
    )


# ============================================================
# IPMS ROOMLIST API
# ============================================================

def fetch_roomlist_night(
    check_in: date,
    check_out: date,
    adults: int = 2,
    children: int = 0,
    rooms_requested: int = 1,
) -> Any:

    if not OPENAPI_KEY:

        raise RuntimeError(
            "IPMS_OPENAPI_KEY is missing from .env"
        )

    if check_out <= check_in:

        raise ValueError(
            "Check-out date must be after "
            "check-in date."
        )

    params = {
        "request_type": "RoomList",

        "HotelCode": HOTEL_CODE,

        "APIKey": OPENAPI_KEY,

        "check_in_date": (
            check_in.isoformat()
        ),

        "check_out_date": (
            check_out.isoformat()
        ),

        "number_adults": adults,

        "number_children": children,

        "num_rooms": rooms_requested,

        "promotion_code": "",

        "property_configuration_info": 0,

        "showtax": 1,

        # IMPORTANT:
        #
        # 0 means we do not hide sold-out room types.
        #
        # This allows the dashboard to display all seven
        # EBC room categories.
        "show_only_available_rooms": 0,

        "show_matched_minimum_nights_rateplans": 1,

        "language": "en",

        "packagefor": "DESKTOP",

        "promotionfor": "DESKTOP",
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            headers=headers,
            timeout=60,
        )

    except requests.RequestException as exc:

        raise RuntimeError(
            f"IPMS request failed: {exc}"
        ) from exc

    if response.status_code != 200:

        raise RuntimeError(
            "IPMS returned HTTP "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    try:

        return response.json()

    except ValueError as exc:

        raise RuntimeError(
            "IPMS returned a non-JSON response."
        ) from exc


# ============================================================
# PARSE ONE NIGHT
# ============================================================

def parse_roomlist_night(
    payload: Any,
    target_date: date,
) -> list[dict]:

    records = extract_room_records(
        payload
    )

    grouped: dict[
        str,
        list[dict]
    ] = {}

    for record in records:

        room_type = canonical_room_type(
            record
        )

        if not room_type:
            continue

        grouped.setdefault(
            room_type,
            []
        ).append(record)

    results = []

    for room_type in ROOM_ORDER:

        config = ROOM_CONFIG[
            room_type
        ]

        candidates = grouped.get(
            room_type,
            []
        )

        # ====================================================
        # AVAILABILITY
        #
        # Multiple rate plans may exist for one room type.
        #
        # We use the maximum available unit count because
        # the underlying room inventory is shared.
        # ====================================================

        ipms_units_left = 0

        for record in candidates:

            available = get_available_units(
                record,
                target_date,
            )

            ipms_units_left = max(
                ipms_units_left,
                available,
            )

        # ====================================================
        # RATE SELECTION
        #
        # If the room is currently available:
        # choose the cheapest available rate plan.
        #
        # If unavailable:
        # choose the cheapest rate we can find for display.
        # ====================================================

        available_rates = []

        all_rates = []

        for record in candidates:

            price = get_price(
                record,
                target_date,
            )

            if price <= 0:
                continue

            all_rates.append(
                (
                    price,
                    record,
                )
            )

            available = get_available_units(
                record,
                target_date,
            )

            if available > 0:

                available_rates.append(
                    (
                        price,
                        record,
                    )
                )

        selected_price = 0.0

        selected_record = None

        if available_rates:

            selected_price, selected_record = min(
                available_rates,
                key=lambda item: item[0],
            )

        elif all_rates:

            selected_price, selected_record = min(
                all_rates,
                key=lambda item: item[0],
            )

        # ====================================================
        # PHYSICAL ROOM CONVERSION
        #
        # Example:
        #
        # Twin:
        # IPMS units = 1
        # rooms/unit = 2
        # physical rooms = 2
        #
        # Villa:
        # IPMS units = 2
        # rooms/unit = 2
        # physical rooms = 4
        # ====================================================

        rooms_per_unit = config[
            "rooms_per_ipms_unit"
        ]

        physical_rooms_left = (
            ipms_units_left
            * rooms_per_unit
        )

        # ====================================================
        # PER PHYSICAL ROOM RATE
        # ====================================================

        if rooms_per_unit > 0:

            per_room_price = (
                selected_price
                / rooms_per_unit
            )

        else:

            per_room_price = (
                selected_price
            )

        # ====================================================
        # AVAILABLE REVENUE
        # ====================================================

        available_room_revenue = (
            physical_rooms_left
            * per_room_price
        )

        selected_tax = 0.0

        if selected_record:

            selected_tax = get_tax(
                selected_record,
                target_date,
            )

        results.append(
            {
                "room_type": room_type,

                "price_per_ipms_unit":
                    selected_price,

                "tax_per_ipms_unit":
                    selected_tax,

                "ipms_units_left":
                    ipms_units_left,

                "rooms_per_unit":
                    rooms_per_unit,

                "physical_inventory":
                    config[
                        "physical_inventory"
                    ],

                "physical_rooms_left":
                    physical_rooms_left,

                "per_room_price":
                    per_room_price,

                "available_room_revenue":
                    available_room_revenue,
            }
        )

    return results


# ============================================================
# GET ONE NIGHT
# ============================================================

def get_night_data(
    check_in: date,
    check_out: date,
) -> dict:

    payload = fetch_roomlist_night(
        check_in=check_in,
        check_out=check_out,
    )

    rooms = parse_roomlist_night(
        payload=payload,
        target_date=check_in,
    )

    return {
        "date": check_in,

        "check_in": check_in,

        "check_out": check_out,

        "rooms": rooms,

        "raw": payload,
    }


# ============================================================
# DATE RANGE
#
# 12-Oct -> 14-Oct
#
# becomes:
#
# 12-Oct -> 13-Oct
# 13-Oct -> 14-Oct
#
# ============================================================

def fetch_date_range(
    from_date: date,
    to_date: date,
) -> list[dict]:

    if to_date <= from_date:

        raise ValueError(
            "To date must be after "
            "From date."
        )

    results = []

    current_date = from_date

    while current_date < to_date:

        next_date = (
            current_date
            + timedelta(days=1)
        )

        results.append(
            get_night_data(
                check_in=current_date,
                check_out=next_date,
            )
        )

        current_date = next_date

    return results


# ============================================================
# NIGHT METRICS
# ============================================================

def calculate_night_metrics(
    night: dict,
) -> dict:

    rooms = night[
        "rooms"
    ]

    total_physical_inventory = sum(
        room[
            "physical_inventory"
        ]
        for room in rooms
    )

    available_physical_rooms = sum(
        room[
            "physical_rooms_left"
        ]
        for room in rooms
    )

    unavailable_physical_rooms = max(
        total_physical_inventory
        - available_physical_rooms,
        0,
    )

    available_revenue = sum(
        room[
            "available_room_revenue"
        ]
        for room in rooms
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # ADR is based ONLY on currently available physical rooms.
    #
    # Example:
    #
    # 7 rooms available
    # ₹95,321 available revenue
    #
    # ADR = ₹95,321 / 7
    # --------------------------------------------------------

    if available_physical_rooms > 0:

        adr = (
            available_revenue
            / available_physical_rooms
        )

    else:

        adr = 0.0

    if total_physical_inventory > 0:

        availability_percent = (
            available_physical_rooms
            / total_physical_inventory
            * 100
        )

    else:

        availability_percent = 0.0

    return {
        "date": night[
            "date"
        ],

        "total_physical_inventory":
            total_physical_inventory,

        "available_physical_rooms":
            available_physical_rooms,

        "unavailable_physical_rooms":
            unavailable_physical_rooms,

        "available_revenue":
            available_revenue,

        "adr":
            adr,

        "availability_percent":
            availability_percent,
    }
"""Minimal SIC-to-NAICS crosswalk for the industries tracked by ECPM.

SEC EDGAR stores each filer's industry under a 4-digit SIC code.
This module maps those SIC codes to the 3-digit NAICS codes used in
our concentration analysis so that EDGAR firms can be slotted into
the correct industry bucket.

Only the ~100 SIC codes relevant to our tracked NAICS sectors are
included — a full crosswalk is unnecessary.
"""

from __future__ import annotations

# SIC 4-digit -> 3-digit NAICS code
# Source: Census Bureau NAICS-to-SIC crosswalk (1997 bridge)
SIC_TO_NAICS: dict[str, str] = {
    # ── NAICS 211: Oil and Gas Extraction ──
    "1311": "211",  # Crude petroleum and natural gas
    "1381": "211",  # Drilling oil and gas wells
    "1382": "211",  # Oil and gas field services
    "1389": "211",  # Services to oil and gas extraction

    # ── NAICS 212: Mining (except Oil and Gas) ──
    "1011": "212",  # Iron ores
    "1021": "212",  # Copper ores
    "1031": "212",  # Lead and zinc ores
    "1041": "212",  # Gold ores
    "1044": "212",  # Silver ores
    "1061": "212",  # Ferroalloy ores
    "1081": "212",  # Metal mining services
    "1094": "212",  # Uranium-radium-vanadium ores
    "1221": "212",  # Bituminous coal and lignite surface mining
    "1222": "212",  # Bituminous coal underground mining
    "1231": "212",  # Anthracite mining
    "1241": "212",  # Coal mining services
    "1400": "212",  # Mining & quarrying nonmetallic minerals
    "1411": "212",  # Dimension stone
    "1422": "212",  # Crushed and broken limestone
    "1442": "212",  # Construction sand and gravel
    "1474": "212",  # Potash, soda, and borate mining
    "1475": "212",  # Phosphate rock

    # ── NAICS 221: Utilities ──
    "4911": "221",  # Electric services
    "4922": "221",  # Natural gas distribution
    "4923": "221",  # Natural gas transmission and distribution
    "4924": "221",  # Natural gas distribution
    "4931": "221",  # Electric and other services combined
    "4932": "221",  # Gas and other services combined
    "4939": "221",  # Combination utilities
    "4941": "221",  # Water supply

    # ── NAICS 236/237: Construction ──
    "1521": "236",  # General contractors - residential
    "1522": "236",  # General contractors - residential (other)
    "1531": "236",  # Operative builders
    "1541": "236",  # General building contractors - industrial
    "1542": "236",  # General building contractors - nonresidential
    "1611": "237",  # Highway and street construction
    "1622": "237",  # Bridge, tunnel, and elevated highway
    "1623": "237",  # Water, sewer, pipeline construction
    "1629": "237",  # Heavy construction nec
    "1731": "237",  # Electrical work

    # ── NAICS 325: Chemical Manufacturing ──
    "2800": "325",  # Chemicals and allied products
    "2810": "325",  # Industrial chemicals
    "2812": "325",  # Alkalies and chlorine
    "2813": "325",  # Industrial gases
    "2816": "325",  # Inorganic pigments
    "2819": "325",  # Industrial inorganic chemicals nec
    "2820": "325",  # Plastics materials and synthetics
    "2821": "325",  # Plastics materials and resins
    "2833": "325",  # Pharmaceutical preparations
    "2834": "325",  # Pharmaceutical preparations
    "2835": "325",  # In vitro diagnostics
    "2836": "325",  # Biological products
    "2840": "325",  # Soap, detergents, and cleaning
    "2842": "325",  # Specialty cleaning, polishing
    "2860": "325",  # Industrial chemicals
    "2869": "325",  # Industrial organic chemicals nec
    "2890": "325",  # Chemical products nec
    "2891": "325",  # Adhesives and sealants
    "2899": "325",  # Chemicals nec

    # ── NAICS 326: Plastics and Rubber ──
    "3080": "326",  # Plastics products
    "3081": "326",  # Plastics plumbing fixtures
    "3082": "326",  # Plastics profile shapes
    "3083": "326",  # Laminated plastics plate, sheet
    "3084": "326",  # Plastics pipe
    "3085": "326",  # Plastics bottles
    "3086": "326",  # Plastics foam products
    "3089": "326",  # Plastics products nec
    "3011": "326",  # Tires and inner tubes
    "3052": "326",  # Rubber and plastics hose and belting

    # ── NAICS 331: Primary Metals ──
    "3310": "331",  # Steel works, blast furnaces
    "3312": "331",  # Steel works, blast furnaces
    "3316": "331",  # Cold-rolled steel sheet
    "3317": "331",  # Steel pipe and tubes
    "3320": "331",  # Iron and steel foundries
    "3330": "331",  # Primary smelting of nonferrous metals
    "3334": "331",  # Primary aluminum
    "3339": "331",  # Primary smelting of nonferrous metals nec
    "3341": "331",  # Secondary smelting of nonferrous metals
    "3350": "331",  # Rolling, drawing of nonferrous metals
    "3357": "331",  # Drawing and insulating of nonferrous wire

    # ── NAICS 332: Fabricated Metal Products ──
    "3411": "332",  # Metal cans
    "3412": "332",  # Metal shipping containers
    "3420": "332",  # Cutlery, hand tools
    "3440": "332",  # Fabricated structural metal
    "3441": "332",  # Fabricated structural metal
    "3443": "332",  # Fabricated plate work - boilers
    "3444": "332",  # Sheet metal work
    "3460": "332",  # Metal forgings and stampings
    "3462": "332",  # Iron and steel forgings
    "3490": "332",  # Misc fabricated metal products

    # ── NAICS 333: Machinery Manufacturing ──
    "3523": "333",  # Farm machinery and equipment
    "3524": "333",  # Lawn and garden equipment
    "3531": "333",  # Construction machinery and equipment
    "3532": "333",  # Mining machinery
    "3533": "333",  # Oil and gas field machinery
    "3537": "333",  # Industrial trucks
    "3540": "333",  # Metalworking machinery
    "3550": "333",  # Special industry machinery
    "3559": "333",  # Special industry machinery nec
    "3561": "333",  # Pumps and pumping equipment
    "3562": "333",  # Ball and roller bearings
    "3580": "333",  # Refrigeration and heating equipment
    "3585": "333",  # Air-conditioning and heating equipment
    "3590": "333",  # Misc industrial machinery

    # ── NAICS 334: Computer and Electronic Products ──
    "3571": "334",  # Electronic computers
    "3572": "334",  # Computer storage devices
    "3574": "334",  # Computer terminals
    "3577": "334",  # Computer peripheral equipment nec
    "3579": "334",  # Office machines nec
    "3661": "334",  # Telephone and telegraph apparatus
    "3663": "334",  # Radio and TV broadcasting equipment
    "3669": "334",  # Communications equipment nec
    "3672": "334",  # Printed circuit boards
    "3674": "334",  # Semiconductors and related devices
    "3677": "334",  # Electronic coils and transformers
    "3678": "334",  # Electronic connectors
    "3679": "334",  # Electronic components nec
    "3812": "334",  # Defense electronics
    "3825": "334",  # Instruments for measuring
    "3827": "334",  # Optical instruments and lenses

    # ── NAICS 335: Electrical Equipment ──
    "3612": "335",  # Power, distribution, and specialty transformers
    "3613": "335",  # Switchgear and switchboard apparatus
    "3621": "335",  # Motors and generators
    "3625": "335",  # Relays and industrial controls
    "3630": "335",  # Household appliances
    "3634": "335",  # Housewares and fans
    "3640": "335",  # Electric lighting and wiring equipment
    "3646": "335",  # Current-carrying wiring devices
    "3648": "335",  # Lighting equipment nec
    "3690": "335",  # Misc electrical equipment
    "3699": "335",  # Electronic components nec

    # ── NAICS 336: Transportation Equipment ──
    "3711": "336",  # Motor vehicles and passenger car bodies
    "3713": "336",  # Truck and bus bodies
    "3714": "336",  # Motor vehicle parts and accessories
    "3715": "336",  # Truck trailers
    "3716": "336",  # Motor homes
    "3720": "336",  # Aircraft and parts
    "3721": "336",  # Aircraft
    "3724": "336",  # Aircraft engines and engine parts
    "3728": "336",  # Aircraft parts nec
    "3731": "336",  # Ship building and repairing
    "3743": "336",  # Railroad equipment
    "3760": "336",  # Guided missiles and space vehicles
    "3761": "336",  # Guided missiles and space vehicles

    # ── NAICS 423: Wholesale Durable Goods ──
    "5040": "423",  # Professional equipment and supplies
    "5045": "423",  # Computers, peripherals, and software
    "5047": "423",  # Medical and hospital equipment
    "5051": "423",  # Metals service centers
    "5063": "423",  # Electrical apparatus and equipment
    "5065": "423",  # Electronic parts and equipment
    "5070": "423",  # Hardware and plumbing

    # ── NAICS 424: Wholesale Nondurable Goods ──
    "5110": "424",  # Paper and paper products
    "5120": "424",  # Drugs, drug proprietaries, and sundries
    "5122": "424",  # Drugs, drug proprietaries, and sundries
    "5130": "424",  # Apparel, piece goods, and notions
    "5140": "424",  # Groceries and related products
    "5141": "424",  # Groceries, general line
    "5149": "424",  # Groceries and related products nec
    "5150": "424",  # Farm-product raw materials
    "5160": "424",  # Chemicals and allied products
    "5169": "424",  # Chemicals, allied products nec

    # ── NAICS 484: Truck Transportation ──
    "4210": "484",  # Trucking and courier services
    "4213": "484",  # Trucking, except local
    "4214": "484",  # Local trucking, with storage
    "4215": "484",  # Courier services (except by air)

    # ── NAICS 517: Telecommunications ──
    "4812": "517",  # Telephone communications
    "4813": "517",  # Telephone communications nec
    "4822": "517",  # Telegraph and other message communications
    "4841": "517",  # Cable and other pay TV services
    "4899": "517",  # Communications services nec

    # ── NAICS 311: Food Manufacturing ──
    "2000": "311",  # Food and kindred products
    "2010": "311",  # Meat products
    "2011": "311",  # Meat packing plants
    "2013": "311",  # Sausages and other prepared meats
    "2015": "311",  # Poultry slaughtering and processing
    "2020": "311",  # Dairy products
    "2024": "311",  # Ice cream and frozen desserts
    "2030": "311",  # Canned, frozen, preserved fruits
    "2040": "311",  # Grain mill products
    "2041": "311",  # Flour and other grain mill products
    "2043": "311",  # Cereal breakfast foods
    "2044": "311",  # Rice milling
    "2050": "311",  # Bakery products
    "2060": "311",  # Sugar and confectionery products
    "2070": "311",  # Fats and oils
    "2080": "311",  # Beverages (also maps to 312)
    "2090": "311",  # Misc food preparations

    # ── NAICS 312: Beverage and Tobacco ──
    "2082": "312",  # Malt beverages
    "2085": "312",  # Distilled and blended liquors
    "2086": "312",  # Bottled and canned soft drinks
    "2111": "312",  # Cigarettes
    "2120": "312",  # Cigars
    "2131": "312",  # Chewing and smoking tobacco

    # ── NAICS 315: Apparel Manufacturing ──
    "2300": "315",  # Apparel and other finished products
    "2310": "315",  # Men's and boys' suits, coats
    "2320": "315",  # Men's and boys' furnishings
    "2330": "315",  # Women's outerwear
    "2340": "315",  # Women's and children's undergarments
    "5130": "315",  # Apparel and piece goods (alt mapping)
    "5136": "315",  # Men's and boys' clothing
    "5137": "315",  # Women's and children's clothing

    # ── NAICS 441: Motor Vehicle Dealers ──
    "5511": "441",  # Motor vehicle dealers (new and used)
    "5521": "441",  # Motor vehicle dealers (used only)
    "5531": "441",  # Auto and home supply stores
    "5571": "441",  # Motorcycle dealers

    # ── NAICS 445: Food and Beverage Stores ──
    "5411": "445",  # Grocery stores
    "5400": "445",  # Food stores
    "5410": "445",  # Grocery stores
    "5412": "445",  # Convenience stores

    # ── NAICS 448: Clothing Stores ──
    "5600": "448",  # Apparel and accessory stores
    "5611": "448",  # Men's clothing stores
    "5621": "448",  # Women's clothing stores
    "5632": "448",  # Women's accessory stores
    "5641": "448",  # Children's clothing stores
    "5651": "448",  # Family clothing stores
    "5661": "448",  # Shoe stores
    "5699": "448",  # Apparel and accessory stores nec

    # ── NAICS 452: General Merchandise Stores ──
    "5311": "452",  # Department stores
    "5331": "452",  # Variety stores
    "5399": "452",  # Misc general merchandise stores

    # ── NAICS 454: Nonstore Retailers ──
    "5961": "454",  # Catalog and mail-order houses
    "5963": "454",  # Direct selling establishments
    "5999": "454",  # Misc retail stores nec

    # ── NAICS 511: Publishing Industries ──
    "2710": "511",  # Newspapers: publishing and printing
    "2711": "511",  # Newspapers: publishing and printing
    "2720": "511",  # Periodicals
    "2731": "511",  # Books: publishing
    "2741": "511",  # Misc publishing
    "7372": "511",  # Prepackaged software
    "7371": "511",  # Computer programming services
    "7374": "511",  # Data processing and hosting

    # ── NAICS 512: Motion Picture and Sound ──
    "7810": "512",  # Motion picture production and services
    "7812": "512",  # Motion picture and tape production
    "7819": "512",  # Motion picture services
    "7820": "512",  # Motion picture distribution
    "7822": "512",  # Motion picture distribution
    "7829": "512",  # Motion picture distribution services
    "7841": "512",  # Video tape rental

    # ── NAICS 621: Ambulatory Health Care ──
    "5912": "621",  # Drug stores and proprietary stores
    "8011": "621",  # Offices and clinics of doctors
    "8049": "621",  # Offices of other health practitioners
    "8060": "621",  # Hospitals (overlaps with 622)
    "8071": "621",  # Health services - medical laboratories
    "8082": "621",  # Home health care services
    "6311": "621",  # Life insurance (health insurers often use this)
    "6321": "621",  # Accident and health insurance
    "6324": "621",  # Hospital and medical service plans

    # ── NAICS 622: Hospitals ──
    "8062": "622",  # General medical and surgical hospitals
    "8063": "622",  # Psychiatric hospitals
    "8069": "622",  # Specialty hospitals

    # ── NAICS 722: Food Services ──
    "5810": "722",  # Eating and drinking places
    "5812": "722",  # Eating places
    "5813": "722",  # Drinking places
}


def sic_to_naics(sic_code: str) -> str | None:
    """Map a 4-digit SIC code to a 3-digit NAICS sector.

    Returns None if no mapping exists for the given SIC code.
    """
    return SIC_TO_NAICS.get(sic_code)


def naics_for_sic(sic_code: str) -> str | None:
    """Try exact match first, then prefix match on the first 3 digits."""
    result = SIC_TO_NAICS.get(sic_code)
    if result:
        return result
    if len(sic_code) >= 3:
        return SIC_TO_NAICS.get(sic_code[:3] + "0")
    return None

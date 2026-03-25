/**
 * BEA summary-level (71 industries) sector code to human-readable name mapping.
 *
 * Source: Bureau of Economic Analysis Input-Output Accounts, Summary Tables.
 * These codes are stable across benchmark years (1997-2022).
 */

import { lookupBeaIoDetailName } from "@/lib/bea-io-detail-names";

export const BEA_SECTOR_NAMES: Record<string, string> = {
  "111CA": "Farms",
  "113FF": "Forestry, fishing & related",
  "211": "Oil & gas extraction",
  "212": "Mining (except oil & gas)",
  "213": "Support activities for mining",
  "22": "Utilities",
  "23": "Construction",
  "321": "Wood products",
  "327": "Nonmetallic mineral products",
  "331": "Primary metals",
  "332": "Fabricated metal products",
  "333": "Machinery",
  "334": "Computer & electronic products",
  "335": "Electrical equipment & appliances",
  "3361MV": "Motor vehicles & parts",
  "3364OT": "Other transportation equipment",
  "337": "Furniture & related products",
  "339": "Miscellaneous manufacturing",
  "311FT": "Food, beverage & tobacco",
  "313TT": "Textile mills & products",
  "315AL": "Apparel & leather",
  "322": "Paper products",
  "323": "Printing & related support",
  "324": "Petroleum & coal products",
  "325": "Chemical products",
  "326": "Plastics & rubber products",
  "42": "Wholesale trade",
  "441": "Motor vehicle & parts dealers",
  "445": "Food & beverage stores",
  "452": "General merchandise stores",
  "4A0": "Other retail",
  "481": "Air transportation",
  "482": "Rail transportation",
  "483": "Water transportation",
  "484": "Truck transportation",
  "485": "Transit & ground passenger transport",
  "486": "Pipeline transportation",
  "487OS": "Other transportation & support",
  "493": "Warehousing & storage",
  "511": "Publishing industries",
  "512": "Motion picture & sound recording",
  "513": "Broadcasting & telecommunications",
  "514": "Data processing & internet services",
  "521CI": "Banking & credit intermediation",
  "523": "Securities & investments",
  "524": "Insurance carriers & related",
  "525": "Funds, trusts & other financial vehicles",
  HS: "Housing",
  ORE: "Other real estate",
  "532RL": "Rental & leasing services",
  "5411": "Legal services",
  "5415": "Computer systems design",
  "5412OP": "Professional, scientific & tech services",
  "55": "Management of companies & enterprises",
  "561": "Administrative & support services",
  "562": "Waste management & remediation",
  "61": "Educational services",
  "621": "Ambulatory health care",
  "622": "Hospitals",
  "623": "Nursing & residential care",
  "624": "Social assistance",
  "711AS": "Arts, entertainment & recreation",
  "713": "Amusements, gambling & recreation",
  "721": "Accommodation",
  "722": "Food services & drinking places",
  "81": "Other services (except government)",
  GFGD: "Federal govt. (defense)",
  GFGN: "Federal govt. (nondefense)",
  GFE: "Federal govt. enterprises",
  GSLG: "State & local govt.",
  GSLE: "State & local govt. enterprises",
  "Used": "Scrap, used & secondhand goods",
  "Other": "Noncomparable imports & rest of world",
  "V001": "Compensation of employees",
  "V002": "Taxes on production & imports",
  "V003": "Gross operating surplus",
  "T005": "Total intermediate",
  "T006": "Total value added",
  "T007": "Total industry output",
  "T008": "Total commodity output",
  "Dept_I": "Dept I (Means of Production)",
  "Dept_II": "Dept II (Means of Consumption)",
};

/**
 * Look up the human-readable name for a BEA sector code.
 * Falls back to detail-level / final-demand labels from official BEA I-O tables, then the code.
 */
export function getSectorName(code: string): string {
  return (
    BEA_SECTOR_NAMES[code] ??
    lookupBeaIoDetailName(code) ??
    code
  );
}

/**
 * Format a label for display: "Code — Name" or just code if unknown.
 */
export function formatSectorLabel(code: string): string {
  const name = BEA_SECTOR_NAMES[code];
  return name ? `${code} — ${name}` : code;
}

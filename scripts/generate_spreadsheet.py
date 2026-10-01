#!/usr/bin/env python3
"""
Generate Azure_Local_HCI_Review_Checklist.xlsx from azure_local_hci_checklist.en.json
and review_checklist_empty.xlsx using Python standard library (zipfile + xml.etree).
Zero external dependencies required.
"""

import json
import os
import zipfile
import xml.etree.ElementTree as ET

BASE_DIR = "/Users/jerry.verghesegeorge/Documents/Az_Local_Review_Scripts"
JSON_PATH = os.path.join(BASE_DIR, "checklists/azure_local_hci_checklist.en.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "spreadsheet/review_checklist_empty.xlsx")
OUTPUT_PATH = os.path.join(BASE_DIR, "spreadsheet/Azure_Local_HCI_Review_Checklist.xlsx")

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", NS_MAIN)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

def make_cell(r, text, style=None, cell_type="inlineStr", formula=None):
    c = ET.Element(f"{{{NS_MAIN}}}c", {"r": r})
    if style:
        c.set("s", str(style))
    if formula:
        f = ET.SubElement(c, f"{{{NS_MAIN}}}f")
        f.text = formula
        if text is not None and text != "":
            v = ET.SubElement(c, f"{{{NS_MAIN}}}v")
            v.text = str(text)
    elif cell_type == "inlineStr":
        c.set("t", "inlineStr")
        is_elem = ET.SubElement(c, f"{{{NS_MAIN}}}is")
        t_elem = ET.SubElement(is_elem, f"{{{NS_MAIN}}}t")
        t_elem.text = str(text) if text is not None else ""
    elif cell_type == "n":
        c.set("t", "n")
        if text is not None and text != "":
            v = ET.SubElement(c, f"{{{NS_MAIN}}}v")
            v.text = str(text)
    return c

def generate_spreadsheet():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    items = data.get("items", [])
    categories = data.get("categories", [])
    checklist_name = data.get("metadata", {}).get("name", "Azure Local (HCI) Review")
    
    row_start = 8
    total_items = len(items)
    last_row = row_start + total_items - 1
    
    # Read existing zip entries
    entries = {}
    with zipfile.ZipFile(TEMPLATE_PATH, "r") as z:
        for name in z.namelist():
            entries[name] = z.read(name)
            
    # -------------------------------------------------------------
    # 1. Update sheet1.xml (Checklist)
    # -------------------------------------------------------------
    root1 = ET.fromstring(entries["xl/worksheets/sheet1.xml"])
    sheetData1 = root1.find(f"{{{NS_MAIN}}}sheetData")
    
    # Update title in A4
    row4 = sheetData1.find(f"./{{{NS_MAIN}}}row[@r='4']")
    if row4 is not None:
        c_a4 = row4.find(f"./{{{NS_MAIN}}}c[@r='A4']")
        if c_a4 is not None:
            row4.remove(c_a4)
        c_new = make_cell("A4", checklist_name, style=2)
        row4.insert(0, c_new)

    # Add dashboard summary metrics in Row 5
    row5 = sheetData1.find(f"./{{{NS_MAIN}}}row[@r='5']")
    if row5 is not None:
        # Clear existing cells in row 5
        for cell in list(row5):
            row5.remove(cell)
        # Add summary KPI formulas
        row5.append(make_cell("A5", f"Total Checks: {total_items}", style=1))
        row5.append(make_cell("C5", "0", style=1, formula=f'COUNTIF(F{row_start}:F{last_row},"Fulfilled")'))
        row5.append(make_cell("D5", "Fulfilled", style=1))
        row5.append(make_cell("E5", "0", style=1, formula=f'COUNTIF(F{row_start}:F{last_row},"Open")'))
        row5.append(make_cell("F5", "Open Action Items", style=1))
        row5.append(make_cell("G5", "0", style=1, formula=f'COUNTIF(F{row_start}:F{last_row},"Not verified")'))
        row5.append(make_cell("H5", "Not Verified", style=1))

    # Remove template placeholder rows 8+
    for r in list(sheetData1.findall(f"./{{{NS_MAIN}}}row")):
        r_num = int(r.attrib.get("r", "0"))
        if r_num >= row_start:
            sheetData1.remove(r)
            
    # Populate checklist items
    for idx, item in enumerate(items):
        r_num = row_start + idx
        row_elem = ET.Element(f"{{{NS_MAIN}}}row", {"r": str(r_num), "spans": "1:16"})
        
        # Mapping:
        # A: Category (s=21)
        # B: Subcategory (s=21)
        # C: Text (s=21)
        # D: Description (s=21)
        # E: Severity (s=21)
        # F: Status (Not verified)
        # G: Comment (blank)
        # H: Link (s=15)
        # I: Training (s=15)
        # J: Graph query (s=22)
        # K: GUID (s=25)
        # L: WAF Pillar (s=25)
        # M: Service (s=25)
        # N: ID (s=25)
        row_elem.append(make_cell(f"A{r_num}", item.get("category", ""), style=21))
        row_elem.append(make_cell(f"B{r_num}", item.get("subcategory", ""), style=21))
        row_elem.append(make_cell(f"C{r_num}", item.get("text", ""), style=21))
        row_elem.append(make_cell(f"D{r_num}", item.get("description", ""), style=21))
        row_elem.append(make_cell(f"E{r_num}", item.get("severity", "Medium"), style=21))
        row_elem.append(make_cell(f"F{r_num}", "Not verified"))
        row_elem.append(make_cell(f"G{r_num}", "", style=21))
        row_elem.append(make_cell(f"H{r_num}", item.get("link", ""), style=15))
        row_elem.append(make_cell(f"I{r_num}", "", style=15))
        row_elem.append(make_cell(f"J{r_num}", item.get("graph", ""), style=22))
        row_elem.append(make_cell(f"K{r_num}", item.get("guid", ""), style=25))
        row_elem.append(make_cell(f"L{r_num}", item.get("waf", ""), style=25))
        row_elem.append(make_cell(f"M{r_num}", item.get("service", ""), style=25))
        row_elem.append(make_cell(f"N{r_num}", item.get("id", ""), style=25))
        
        sheetData1.append(row_elem)
        
    # Update autoFilter range to encompass all rows
    af = root1.find(f".//{{{NS_MAIN}}}autoFilter")
    if af is not None:
        af.set("ref", f"A7:N{last_row}")
        
    # Update or add DataValidation for column F
    dv_list = root1.find(f"./{{{NS_MAIN}}}dataValidations")
    if dv_list is None:
        # insert before conditionalFormatting or printOptions or at end
        dv_list = ET.SubElement(root1, f"{{{NS_MAIN}}}dataValidations", {"count": "1"})
        dv = ET.SubElement(dv_list, f"{{{NS_MAIN}}}dataValidation", {
            "type": "list",
            "allowBlank": "1",
            "showInputMessage": "0",
            "showErrorMessage": "0",
            "showDropDown": "0",
            "sqref": f"F{row_start}:F{last_row}"
        })
        f1 = ET.SubElement(dv, f"{{{NS_MAIN}}}formula1")
        f1.text = "=Values!$B$2:$B$6"
    else:
        dv = dv_list.find(f"./{{{NS_MAIN}}}dataValidation")
        if dv is not None:
            dv.set("sqref", f"F{row_start}:F{last_row}")
            dv.set("type", "list")
            f1 = dv.find(f"./{{{NS_MAIN}}}formula1")
            if f1 is None:
                f1 = ET.SubElement(dv, f"{{{NS_MAIN}}}formula1")
            f1.text = "=Values!$B$2:$B$6"

    # Save sheet1.xml back
    entries["xl/worksheets/sheet1.xml"] = ET.tostring(root1, encoding="utf-8", xml_declaration=True)
    
    # -------------------------------------------------------------
    # 2. Update sheet2.xml (Values)
    # -------------------------------------------------------------
    root2 = ET.fromstring(entries["xl/worksheets/sheet2.xml"])
    sheetData2 = root2.find(f"{{{NS_MAIN}}}sheetData")
    
    # Update Categories in column C (rows 2 to 2 + len(categories))
    for idx, cat in enumerate(categories):
        r_num = 2 + idx
        row = sheetData2.find(f"./{{{NS_MAIN}}}row[@r='{r_num}']")
        if row is None:
            row = ET.SubElement(sheetData2, f"{{{NS_MAIN}}}row", {"r": str(r_num)})
        c_elem = row.find(f"./{{{NS_MAIN}}}c[@r='C{r_num}']")
        if c_elem is not None:
            row.remove(c_elem)
        row.append(make_cell(f"C{r_num}", cat.get("name", "")))
        
    entries["xl/worksheets/sheet2.xml"] = ET.tostring(root2, encoding="utf-8", xml_declaration=True)
    
    # -------------------------------------------------------------
    # 3. Update workbook.xml (FilterDatabase definedName)
    # -------------------------------------------------------------
    root_wb = ET.fromstring(entries["xl/workbook.xml"])
    dn = root_wb.find(f".//{{{NS_MAIN}}}definedName[@name='_xlnm._FilterDatabase']")
    if dn is not None:
        dn.text = f"'Checklist'!$A$7:$N${last_row}"
    entries["xl/workbook.xml"] = ET.tostring(root_wb, encoding="utf-8", xml_declaration=True)

    # -------------------------------------------------------------
    # 4. Write new XLSX
    # -------------------------------------------------------------
    with zipfile.ZipFile(OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as z_out:
        for name, data_bytes in entries.items():
            z_out.writestr(name, data_bytes)
            
    print(f"Successfully generated {OUTPUT_PATH} with {total_items} items (rows {row_start} to {last_row}).")

if __name__ == "__main__":
    generate_spreadsheet()

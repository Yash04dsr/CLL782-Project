
import re
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
import traceback

# Setup matplotlib for math rendering
plt.rcParams['text.usetex'] = False 
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.serif'] = ['Times New Roman']

def render_math_to_image(formula, fontsize=12):
    """Renders a LaTeX formula to an image (BytesIO) using matplotlib."""
    # Fix common latex compatibility issues with mathtext
    formula = re.sub(r'\\le\b', r'\\leq', formula)
    formula = re.sub(r'\\ge\b', r'\\geq', formula)

    # Use a fixed aspect ratio for consistency, but maybe variable width is better?
    # A4 width is ~210mm. If we want high res, we generated at 300dpi.
    # Let's use a reasonable box.
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.set_size_inches(8, 1.5) # 8 inches wide, 1.5 inches high.
    
    if not formula.strip():
        return None

    try:
        text = fig.text(0.5, 0.5, f"${formula}$", fontsize=fontsize, ha='center', va='center')
        buf = BytesIO()
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error rendering math formula '{formula}': {e}")
        return None

class PDFReport(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.equation_counter = 1

    def header(self):
        self.set_font('Times', '', 9)
        self.cell(0, 10, 'CLL782: Process Optimization Module 3.3: Waste Logistics', align='R')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Times', '', 9)
        self.cell(0, 10, f'{self.page_no()}', align='C')

    def add_markdown_content(self, md_text):
        lines = md_text.split('\n')
        buffer_text = []

        def flush_text():
            if buffer_text:
                txt = " ".join(buffer_text)
                self.set_x(self.l_margin) 
                self.set_font("Times", "", 12) 
                
                txt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', txt)
                txt = re.sub(r'\*(.*?)\*', r'<i>\1</i>', txt)
                txt = re.sub(r'\$([^$]+)\$', r'<i>\1</i>', txt)

                try:
                    self.write_html(txt)
                except Exception as e:
                    self.multi_cell(0, 5, txt)
                
                self.ln(6) 
                buffer_text.clear()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('<!--'): 
                i+=1
                continue

            # Headers
            if line.startswith('#'):
                flush_text()
                level = len(line.split(' ')[0])
                text = line.lstrip('#').strip()
                size = 16 if level == 1 else 14 if level == 2 else 12
                self.set_x(self.l_margin)
                self.set_font("Times", "B", size)
                
                if "Project Report" in text or "Module 3.2" in text:
                     self.cell(0, 8, text, align='C', ln=True)
                else:
                     self.multi_cell(0, 8, text)
                
                self.ln(4)
                self.set_font("Times", "", 12)
            
            # Horizontal rule
            elif line.startswith('---'):
                flush_text()
                self.ln(2)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.ln(5)
            
            # List items
            elif line.startswith('- ') or line.startswith('* '):
                flush_text() 
                self.set_font("Times", "", 12)
                self.set_x(self.l_margin + 6) 
                content = line[2:]
                
                content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
                content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)
                content = re.sub(r'\$([^$]+)\$', r'<i>\1</i>', content)
                
                self.cell(5, 5, chr(149), align='R')
                
                try:
                    self.write_html(content)
                except:
                     self.multi_cell(0, 5, content)
                
                self.ln(2)
                self.set_x(self.l_margin) 

            # Table
            elif "|" in line:
                flush_text()
                table_lines = []
                while i < len(lines) and "|" in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                i -= 1 
                
                table_data = []
                for row_line in table_lines:
                    if '---' in row_line: continue 
                    row = [c.strip() for c in row_line.strip('|').split('|')]
                    table_data.append(row)
                
                if table_data:
                    self.set_font("Times", "", 10) 
                    self.ln(2)
                    try:
                         with self.table(text_align='L') as table:
                             for idx, row in enumerate(table_data):
                                 row_obj = table.row()
                                 if idx == 0:
                                     self.set_font("Times", "B", 10)
                                 else:
                                     self.set_font("Times", "", 10)
                                     
                                 for datum in row:
                                     datum = datum.replace('$', '')
                                     row_obj.cell(datum)
                    except Exception as e:
                        print(f"Table rendering error: {e}")
                        self.set_font("courier", "", 9)
                        for row_line in table_lines:
                             self.multi_cell(0, 4, row_line)

                    self.ln(4)


            # Display Math
            elif line.startswith('$$'):
                flush_text()
                formula = line.strip('$')
                # Check block
                if not line.endswith('$$') or line == '$$':
                   j = i + 1
                   formula = ""
                   if line != '$$': formula += line.lstrip('$')
                   while j < len(lines):
                       if lines[j].strip().endswith('$$'):
                           formula += " " + lines[j].strip().rstrip('$')
                           i = j
                           break
                       formula += " " + lines[j].strip()
                       j += 1
                
                print(f"Rendering math: {formula}")
                img_buf = render_math_to_image(formula, fontsize=14)
                self.set_x(self.l_margin)
                if img_buf:
                    # Logic to calculate dimensions
                    # We want to place image.
                    # We set width to 50% of page width.
                    img_target_width = self.w * 0.5
                    
                    # We need the aspect ratio to know height.
                    # img_buf contains a PNG. We can read it with PIL or just rely on fpdf to place it?
                    # fpdf.image() doesn't return height.
                    # But we generated it with matplotlib.
                    # We can assume a default aspect for safe spacing, or read headers.
                    # Or simpler: matplotlib `savefig` with `bbox_inches='tight'` creates variable size.
                    # Let's peek at the image using PIL? No PIL module imported.
                    
                    # Let's guess/calculate from Matplotlib settings.
                    # No, bbox_tight makes it variable.
                    
                    # Alternative: Let FPDF calculate it?
                    # self.image(..., h=0) maintains aspect ratio.
                    # But we need to know how much Y increased.
                    
                    y_before = self.get_y()
                    
                    if y_before > 240: 
                        self.add_page()
                        y_before = self.get_y()
                    
                    # Place image.
                    self.image(img_buf, w=img_target_width, x=(self.w - img_target_width)/2)
                    
                    # Since we don't know the height fpdf used interactively easily without checking the object,
                    # We can assume a max height or safe buffer. 
                    # Most single line formulas will be around 1-2cm high.
                    # Let's allocate 20mm for now, or use a heuristic.
                    # BETTER: Use a fixed height for the image in Matplotlib if possible? No, tight bbox is good.
                    
                    # Hack: Read the last inserted image info from fpdf structure if possible?
                    # fpdf.images is a dict.
                    # keys are hashes.
                    
                    # Let's just be generous with spacing.
                    # A typical formula line isn't taller than 25mm (1 inch) usually.
                    # Let's shift Y by 20mm.
                    
                    # Wait, if I don't update Y, `ln` updates from LAST Y?
                    # `self.image` does NOT update Y.
                    # So `y_after` is still `y_before`.
                    # I must manually set Y.
                    
                    # Let's estimate height based on 8:1.5 ratio from figure size?
                    # 8 width : 1.5 height.
                    # But we used bbox_tight, so it stripped whitespace.
                    # The height is likely much less than 1.5 inches (38mm) relative to width.
                    
                    # Let's try 15mm as base + 5mm padding = 20mm.
                    
                    img_height = 20 # Approximation
                    
                    # Equation number
                    self.set_xy(self.w - 20, y_before + img_height/2 - 2)
                    self.set_font("Times", "", 12)
                    self.cell(10, 10, f"({self.equation_counter})")
                    self.equation_counter += 1
                    
                    # Move cursor below image
                    self.set_y(y_before + img_height + 5)
                    
                else:
                    self.set_font("courier", "", 10)
                    self.multi_cell(0, 5, formula, align='C')
            
            # Blank line
            elif not line:
                flush_text()
                self.ln(3) 
            
            else:
                buffer_text.append(line)
                
            i += 1
        
        flush_text()

try:
    with open('Module_3_3_Report.md', 'r') as f:
        md_content = f.read()

    pdf = PDFReport()
    pdf.add_page()
    pdf.add_markdown_content(md_content)
    pdf.output('Module_3_3_Report.pdf')
    print("PDF Generated successfully: Module_3_3_Report.pdf")

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

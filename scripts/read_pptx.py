import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        # pptx uses namespace schemas, we can ignore them by just searching for text nodes
        # The text is usually in <a:t> elements
        texts = []
        for elem in root.iter():
            if elem.tag.endswith('}t') and elem.text:
                texts.append(elem.text)
        return " ".join(texts)
    except Exception as e:
        return f"Error parsing XML: {e}"

def extract_pptx_content(pptx_path):
    if not os.path.exists(pptx_path):
        print(f"File not found: {pptx_path}")
        return

    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            # Get list of files
            filelist = z.namelist()
            
            # Find slides and notes
            slides = [f for f in filelist if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
            notes = [f for f in filelist if f.startswith('ppt/notesSlides/notesSlide') and f.endswith('.xml')]
            
            # Sort them to process in order
            def sort_key(filename):
                # Extract number from 'ppt/slides/slide1.xml' or 'ppt/notesSlides/notesSlide1.xml'
                name = os.path.basename(filename)
                num_str = ''.join(c for c in name if c.isdigit())
                return int(num_str) if num_str else 0
                
            slides.sort(key=sort_key)
            notes.sort(key=sort_key)
            
            # Read relationship mappings
            # To map slides to notes correctly, we need _rels
            # But for simplicity, let's just output slides and their matching notes based on slide id (this is an approximation, real mapping is in _rels)
            # Actually, let's just extract all notes and slides
            
            print("=== SLIDES AND NOTES ===")
            
            for slide_path in slides:
                slide_num = sort_key(slide_path)
                print(f"\n--- Slide {slide_num} ---")
                slide_xml = z.read(slide_path)
                slide_text = extract_text_from_xml(slide_xml)
                print("CONTENT:", slide_text[:500] + ("..." if len(slide_text) > 500 else ""))
                
                # Check for corresponding notes slide
                # We can check relations but often they loosely align, or we can just parse all notes and see if they mention the slide.
                # Let's just do a naive mapping or list notes separately
            
            print("\n=== NOTES SLIDES ===")
            for note_path in notes:
                note_num = sort_key(note_path)
                note_xml = z.read(note_path)
                note_text = extract_text_from_xml(note_xml)
                if note_text.strip():
                    print(f"\n--- Note File {note_num} ---")
                    print(note_text)
                    
    except Exception as e:
        print(f"Error reading pptx: {e}")

if __name__ == '__main__':
    extract_pptx_content('paper/588-Project-Presentation.pptx')

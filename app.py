import gradio as gr
from PIL import Image, ImageOps
import zipfile
import io
import os

# 300 DPI Dimensions (Width x Height)
SIZES = {
    "A3": (3508, 4960),
    "A4": (2480, 3508),
    "A5": (1748, 2480),
    "US_Letter": (2550, 3300),
    "US_11x14": (3300, 4200)
}

def process_images(input_img, formats, strategy):
    if input_img is None:
        return None
    
    zip_path = "printable_package.zip"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, size in SIZES.items():
            # Handle Aspect Ratio
            if strategy == "Crop (Fill Canvas)":
                resized = ImageOps.fit(input_img, size, Image.Resampling.LANCZOS)
            else:
                resized = ImageOps.pad(input_img, size, Image.Resampling.LANCZOS, color=(255, 255, 255))
            
            # Save selected formats
            for fmt in formats:
                buffer = io.BytesIO()
                # Remove transparency for JPG/PDF
                final_img = resized.convert("RGB") if fmt in ["JPG", "PDF"] else resized
                
                if fmt == "PDF":
                    final_img.save(buffer, format="PDF", resolution=300.0)
                elif fmt == "JPG":
                    final_img.save(buffer, format="JPEG", quality=95)
                else:
                    final_img.save(buffer, format="PNG")
                
                zf.writestr(f"{name}.{fmt.lower()}", buffer.getvalue())
                
    return zip_path

# Create the Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎨 High-Res Printable Automator")
    gr.Markdown("Upload your upscaled master. Choose your settings. Get a ZIP with everything.")
    
    with gr.Row():
        with gr.Column():
            img_input = gr.Image(type="pil", label="1. Upload Master PNG/JPG")
            formats = gr.CheckboxGroup(["PNG", "JPG", "PDF"], label="2. Export Formats", value=["PNG", "PDF"])
            strategy = gr.Radio(["Crop (Fill Canvas)", "Pad (White Borders)"], label="3. Aspect Ratio Strategy", value="Pad (White Borders)")
            run_btn = gr.Button("Generate Files", variant="primary")
            
        with gr.Column():
            file_output = gr.File(label="4. Download ZIP Package")

    run_btn.click(
        fn=process_images, 
        inputs=[img_input, formats, strategy], 
        outputs=file_output
    )

demo.launch()

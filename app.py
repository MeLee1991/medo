import streamlit as st
from PIL import Image, ImageOps
import io
import zipfile


# Define target dimensions at 300 DPI (Width x Height)
DIMENSIONS_300_DPI = {
    "A3 (11.7 x 16.5 in)": (3508, 4960),
    "A4 (8.3 x 11.7 in)": (2480, 3508),
    "A5 (5.8 x 8.3 in)": (1748, 2480),
    "US Letter (8.5 x 11 in)": (2550, 3300),
    "11x14 in": (3300, 4200)
}


def process_image(img, target_size, aspect_mode):
    """Resizes the image based on the chosen aspect ratio strategy."""
    if aspect_mode == "Crop (Fill canvas, lose margins)":
        return ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
    else:
        # Pad (Fit inside canvas, add white borders)
        return ImageOps.pad(img, target_size, method=Image.Resampling.LANCZOS, color=(255, 255, 255))


def convert_to_format(img, format_type):
    """Prepares the image for the specific export format."""
    # JPG and PDF do not support transparency (RGBA), so we convert to RGB
    if format_type in ["JPG", "PDF"] and img.mode in ("RGBA", "P"):
        return img.convert("RGB")
    return img


st.set_page_config(page_title="Printable Resizer & Converter", layout="centered")


st.title("🖨️ Master File Resizer & Exporter")
st.write("Upload your upscaled master file, and this tool will automatically resize, fix aspect ratios, and convert to your needed formats.")


st.divider()


# 1. File Upload
uploaded_file = st.file_uploader("Upload Master Image (PNG or JPG)", type=["png", "jpg", "jpeg"])


if uploaded_file is not None:
    # Display preview
    original_img = Image.open(uploaded_file)
    st.image(original_img, caption="Original Master File Preview", use_container_width=True)
    
    st.divider()
    
    # 2. Configuration Options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("1. Target Sizes")
        selected_sizes = []
        for size_name in DIMENSIONS_300_DPI.keys():
            if st.checkbox(size_name, value=True):
                selected_sizes.append(size_name)
                
    with col2:
        st.subheader("2. Aspect Ratio Fix")
        st.write("How to handle US vs EU size shifts:")
        aspect_mode = st.radio(
            "Strategy:",
            ["Crop (Fill canvas, lose margins)", "Pad (Fit inside, add white borders)"]
        )
        
    with col3:
        st.subheader("3. Export Formats")
        export_png = st.checkbox("PNG", value=True)
        export_jpg = st.checkbox("JPG", value=True)
        export_pdf = st.checkbox("PDF", value=True)
        
        selected_formats = []
        if export_png: selected_formats.append("PNG")
        if export_jpg: selected_formats.append("JPG")
        if export_pdf: selected_formats.append("PDF")


    st.divider()


    # 3. Execution & ZIP Generation
    if st.button("Generate Printables", type="primary", use_container_width=True):
        if not selected_sizes or not selected_formats:
            st.error("Please select at least one size and one format.")
        else:
            with st.spinner("Processing images... This might take a moment."):
                
                # Create an in-memory ZIP file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    
                    for size_name in selected_sizes:
                        target_size = DIMENSIONS_300_DPI[size_name]
                        
                        # Resize the image once per size
                        resized_img = process_image(original_img, target_size, aspect_mode)
                        
                        # Clean up the filename
                        clean_size_name = size_name.split(" ")[0] # e.g., "A3", "US", "11x14"
                        base_filename = f"Printable_{clean_size_name}"
                        
                        for fmt in selected_formats:
                            # Convert color modes if necessary
                            final_img = convert_to_format(resized_img, fmt)
                            
                            # Save to in-memory bytes
                            img_byte_arr = io.BytesIO()
                            
                            if fmt == "PDF":
                                final_img.save(img_byte_arr, format="PDF", resolution=300.0)
                                filename = f"{base_filename}.pdf"
                            elif fmt == "JPG":
                                final_img.save(img_byte_arr, format="JPEG", quality=95)
                                filename = f"{base_filename}.jpg"
                            else:
                                final_img.save(img_byte_arr, format="PNG")
                                filename = f"{base_filename}.png"
                                
                            # Write the bytes to the ZIP file
                            zip_file.writestr(filename, img_byte_arr.getvalue())


                # Provide the download button
                st.success("✅ All files processed successfully!")
                st.download_button(
                    label="⬇️ Download All as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="Processed_Printables.zip",
                    mime="application/zip",
                    use_container_width=True
                )
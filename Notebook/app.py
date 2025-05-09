import streamlit as st
from PIL import Image
import io
import numpy as np

def encode_message(image, secret_message):
    from PIL import Image
    import numpy as np

    # Convert to RGB if RGBA
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # Image to array
    img_array = np.array(image)

    # Message to binary
    binary_message = ''.join(format(ord(c), '08b') for c in secret_message)

    # Add length prefix (32 bits)
    message_len = format(len(binary_message), '032b')  # Supports up to ~4.2 billion bits
    full_message = message_len + binary_message

    # Check space
    max_bits = img_array.shape[0] * img_array.shape[1] * 3
    if len(full_message) > max_bits:
        return None, "Image too small to encode this message"

    # Flatten for easier access
    flat_img = img_array.flatten()

    # Encode each bit
    idx = 0
    for i in range(len(full_message)):
        channel_idx = idx
        if idx % 4 == 3:  # Skip alpha channel if it somehow sneaks in
            idx += 1
            channel_idx = idx

        # Set LSB to the bit
        flat_img[channel_idx] = (flat_img[channel_idx] & 0b11111110) | int(full_message[i])
        idx += 1

    # Reshape and convert back
    encoded_img_array = flat_img.reshape(img_array.shape)
    encoded_image = Image.fromarray(encoded_img_array)

    return encoded_image, None
def decode_message(image):
    import numpy as np

    # Convert to RGB if RGBA
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # Image to array
    img_array = np.array(image)

    # Flatten image
    flat_img = img_array.flatten()

    # Extract LSBs
    bits = []
    idx = 0
    while len(bits) < 32:  # First 32 bits = length prefix
        if idx % 4 == 3:  # Skip alpha channel if present
            idx += 1
            continue
        bits.append(str(flat_img[idx] & 1))
        idx += 1

    # Get message length from first 32 bits
    message_length = int(''.join(bits), 2)

    # Now read the actual message bits
    bits = []
    while len(bits) < message_length:
        if idx % 4 == 3:
            idx += 1
            continue
        bits.append(str(flat_img[idx] & 1))
        idx += 1

    # Convert bits to characters
    message = ''
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        char = chr(int(''.join(byte), 2))
        message += char

    return message

# Set up the Streamlit app
st.set_page_config(page_title="Image Steganography App", layout="wide")

st.title("Image Steganography")
st.write("Hide secret messages in images using LSB (Least Significant Bit) encoding")

# Create tabs for encode and decode
tab1, tab2 = st.tabs(["Encode Message", "Decode Message"])

# Encode tab
with tab1:
    st.header("Encode a Secret Message")

    # Upload image
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], key="encode_upload")

    if uploaded_file is not None:
        # Display the uploaded image
        original_image = Image.open(uploaded_file)

        # Calculate maximum message size
        max_chars = (original_image.width * original_image.height * 3) // 8 - 1  # -1 for null terminator

        col1, col2 = st.columns(2)
        with col1:
            st.image(original_image, caption="Original Image", use_column_width=True)

        # Input for secret message
        secret_message = st.text_area("Enter your secret message",
                                    height=100,
                                    max_chars=max_chars,
                                    help=f"Maximum {max_chars} characters")

        # Encode button
        if st.button("Encode Message", key="encode_btn"):
            if not secret_message:
                st.error("Please enter a message to hide")
            else:
                # Encode the message
                with st.spinner("Encoding message..."):
                    encoded_image, error = encode_message(original_image, secret_message)

                if error:
                    st.error(error)
                else:
                    # Display the encoded image
                    with col2:
                        st.image(encoded_image, caption="Image with Hidden Message", use_column_width=True)

                    # Option to download the encoded image
                    buf = io.BytesIO()
                    encoded_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()

                    st.download_button(
                        label="Download Encoded Image",
                        data=byte_im,
                        file_name="encoded_image.png",
                        mime="image/png"
                    )

# Decode tab
with tab2:
    st.header("Decode a Hidden Message")

    # Upload image to decode
    decode_uploaded_file = st.file_uploader("Upload an image with a hidden message", type=["png", "jpg", "jpeg"], key="decode_upload")

    if decode_uploaded_file is not None:
        # Display the uploaded image
        encoded_image = Image.open(decode_uploaded_file)
        st.image(encoded_image, caption="Image to Decode", width=400)

        # Decode button
        if st.button("Decode Message", key="decode_btn"):
            with st.spinner("Decoding message..."):
                decoded_message = decode_message(encoded_image)

            if decoded_message:
                st.success("Message decoded successfully!")
                st.subheader("Decoded Message:")
                st.write(f'"{decoded_message}"')
                st.text_area("Copy decoded message", value=decoded_message, height=150)
            else:
                st.error("No hidden message found or error in decoding")

# Add information section
st.sidebar.title("About")
st.sidebar.info(
    """
    This app demonstrates LSB Steganography - the technique of hiding information within an image by modifying the least significant bit of pixel values.

    **How it works:**
    1. Each character of your message is converted to its binary representation
    2. The least significant bit of each color channel in the image is modified to store your message
    3. The resulting image looks nearly identical to the original

    **Notes:**
    - Use PNG format for best results
    - All processing happens in your browser - no data is sent to any server
    """
)

st.sidebar.title("Tips")
st.sidebar.markdown(
    """
    - Larger images can store longer messages
    - The encoded image is saved in PNG format to preserve all data
    - For best results, use images without compression
    """
)

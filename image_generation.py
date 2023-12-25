from openai import OpenAI
import base64
import time
import requests


client = OpenAI(api_key="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")


# Function to encode image to base64 format and then deconde file to utf-8 string
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



# function for vision API description call
def vision_api_describe_image(image_base64):
    response = client.chat.completions.create(
        model = "gpt-4-vision-preview",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Describe the image in detail (color, features, theme, style, etc)"
                    }
                ],
            }
        ],
        max_tokens=300,
    )
    # Accessing the content correctly
    description_text = response.choices[0].message.content
    return description_text


# Function for generating an image with DALL-E API
def dalle_api_generate_image(descripiton):
    response = client.images.generate(
        model="dall-e-3",
        prompt=descripiton,
        size="1024x1024",
        quality="standard",
        n=1
    )
    return response.data[0].url


# Function for the Vision API comparison and improved descripiton call
def vision_api_comapare_and_describe(reference_image_base64, synthetic_image_base64):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{reference_image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Describe both images in detail (colors, features, theme, styoe, etc), then compare them. Finally create a new and improved description prompt to match the robotic image as close as possible."
                    },
                    {
                        "type": "image_url",
                        "image_url":{
                            "url": f"data:image/jpeg;base64,{synthetic_image_base64}"
                        }
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    # Accessing the content correctly
    improved_description_text = response.choices[0].message.content
    return improved_description_text
    

# Main function 
def iterative_image_synthesis(reference_image_path, iteration=5):
    reference_image_base64 = encode_image_to_base64(reference_image_path)
    descriptions = []
    synthetic_images_urls = []

    for i in range(iteration):
        if i==0:
            # initial description from the reference image
            description = vision_api_describe_image(reference_image_base64)
        else:
            # Get an improved description by comparing the reference and the latest synthetic image
            description = vision_api_comapare_and_describe(
                reference_image_base64, synthetic_image_base64
            )
        descriptions.append(description)

        # Fine_tune the description by parsing the key elements
        # for simplicity, we'll just add "high details" to the description to prompt DALL-E for more detail
        # In practice, you would parse the description and extrace more nuanced improvements
        fine_tuned_description = f"{description} in high detail. Make the image more robotic and AI driven."

        synthetic_images_url = dalle_api_generate_image(fine_tuned_description)
        synthetic_images_urls.append(synthetic_images_url)

        # Fetch the synthetic image from the URL
        Synthetic_image_response = requests.get(synthetic_images_url)
        if Synthetic_image_response.status_code == 200:
            synthetic_image_content = Synthetic_image_response.content
            synthetic_image_base64 = base64.b64encode(synthetic_image_content).decode('utf-8')

            # Save the synthetic imae content to a file
            synthetic_image_path = f"Ref_image/synthetic_image_{i}.png"
            with open(synthetic_image_path, 'wb') as image_file:
                image_file.write(synthetic_image_content)
            print(f"Synthetic image saved at {synthetic_image_path}")
        else:
            print(f"Failed to fetch synthetic image for iteration {i+1}: Status code {Synthetic_image_response.status_code}")
            # Skip the iteration if image couldn't be fetched
            continue

        # Automated Quality check (simple version)
        # Here we are using the length of the description as a proxy for detail
        # A more sophisticated approach would be needed for a real application
        current_description_length = len(description)
        if i>0 and current_description_length <= len(description[-2]):
            print(f"No significant improvement in detail detected in iteration {i+1}.")
            # Optionally, we could decide to stop iteration if there's no improvement
            
        
        print(f"Iteration {i+1}: Description: {fine_tuned_description}")

        time.sleep(6) # Sleep to avoid hitting API rate limits

    return description, synthetic_images_urls


reference_image_path = "Ref_image/input_image.jpeg"

iterative_image_synthesis(reference_image_path)
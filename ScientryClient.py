
from gradio_client import Client
import json
import requests
import gradio as gr
import ast

def upload_pdf(pdf_path):
    api_url = "https://tmpfiles.org/api/v1/upload"
    with open(pdf_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(api_url, files=files)
    url = response.json()['data']['url']
    download_url = f"https://tmpfiles.org/dl/{url.split('.org/')[-1]}"
    return download_url

def fetch_doi_data(pdf_path):
    pdf_url = upload_pdf(pdf_path)
    client = Client("raannakasturi/ScientryPDFDataAPI")
    result = client.predict(pdf_url=pdf_url, api_name="/getDOIData")
    result = json.loads(result)
    return pdf_url, result

def generate_summary_mindmap(pdf_url, doi):
    client = Client("raannakasturi/ScientryAPI")
    result = client.predict(
        url=pdf_url,
        id=doi,
        access_key="scientrypass",
        api_name="/rexplore_summarizer"
    )
    return result

def generate_mindmap(markdown_mindmap):
    client = Client("raannakasturi/MindMap")
    result = client.predict(
            mindmap_markdown=markdown_mindmap,
            api_name="/generate"
    )
    return result

def create_files(title, content, file_type):
    file_name = f"{title}.{file_type}"
    if isinstance(content, str) and content.startswith("b'"):
        content = ast.literal_eval(content)
    with open(file_name, "wb") as file:
        file.write(content)
    return file_name


def main(pdf_path):
    pdf_url, doi_data = fetch_doi_data(pdf_path)
    summary_mindmap = generate_summary_mindmap(pdf_url, doi_data["doi"])
    markdown_summary = summary_mindmap[1]
    markdown_mindmap = summary_mindmap[2]
    result = generate_mindmap(markdown_mindmap)
    if not result:
        mindmap_svg_file = ""
        mindmap_pdf_file = ""
    else:
        mindmap_svg_file = create_files(doi_data["title"], result[0], "svg")
        mindmap_pdf_file = create_files(doi_data["title"], result[1], "pdf")
    return doi_data["citation_text"], doi_data["title"], markdown_summary, mindmap_svg_file, mindmap_pdf_file

def generate_pdf_summary_mindmap(pdf):
    pdf_path = pdf.name
    citation, title, markdown_summary, mindmap_svg_file, mindmap_pdf_file = main(pdf_path)
    return citation, title, markdown_summary, mindmap_svg_file, mindmap_pdf_file

def download_file(download_as_pdf):
    return download_as_pdf


with gr.Blocks(title="Scientry Local App") as app:
    gr.HTML("""
<div class="flex flex-col justify-center items-center w-full pt-10">
        <div class="flex justify-center items-center space-x-2">
            <img src="https://github.com/RaannaKasturi/ScientryLocal/blob/main/icon.png" alt="ScientryIcon" width="32" height="32">
            <h1 class="text-3xl font-bold">Scientry (Local)</h1>
        </div>
        <p class="italic">Science Simplifed, Knowledge Amplified</p>
        <br>
        <p>Designed and Developed by <a class="underline underline-offset-2" href="http://nayankasturi.eu.org"
                target="_blank" rel="noopener noreferrer">Nayan Kasturi</a> and <a class="underline underline-offset-2"
                href="http://binarybiology.top" target="_blank" rel="noopener noreferrer">Binary Biology</a></p>
    </div>
""")
    with gr.Column():
        with gr.Row():
            with gr.Column():
                pdf = gr.File(file_count='single', file_types=[".pdf"], label="Upload PDF")
                generate = gr.Button(value="Generate")
            with gr.Column():
                title = gr.Textbox(label="Title", placeholder="Title will be displayed here", show_copy_button=True)
                citation = gr.Textbox(label="Citation", placeholder="Citation will be displayed here", show_copy_button=True)
        with gr.Row():
            summary = gr.Textbox(label="Summary", placeholder="Summary will be displayed here", interactive=True, show_copy_button=True)
            with gr.Column():
                download_as_svg = gr.DownloadButton(label="Download as SVG")
                download_as_pdf = gr.DownloadButton(label="Download as PDF")
    generate.click(generate_pdf_summary_mindmap, inputs=[pdf], outputs=[citation, title, summary, download_as_svg, download_as_pdf])
    download_as_svg.click(download_file, inputs=[download_as_svg], outputs=[download_as_svg])
    download_as_pdf.click(download_file, inputs=[download_as_pdf], outputs=[download_as_pdf])

app.launch(inbrowser=True, show_api=False)


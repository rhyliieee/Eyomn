# ---
# args: ["--force-download"]
# ---
import modal
import os

MODELS_DIR = "/eyomn_model_volume"

DEFAULT_NAME = "m42-health/Llama3-Med42-8B"
#DEFAULT_REVISION = "a7c09948d9a632c2c840722f519672cd94af885d"

volume = modal.Volume.from_name("eyomn_model_volume", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        [
            "huggingface_hub",  # download models from the Hugging Face Hub
            "hf-transfer",  # download models faster with Rust
        ]
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)


MINUTES = 60
HOURS = 60 * MINUTES


app = modal.App(
    image=image, secrets=[modal.Secret.from_name("RAG_APP_SECRETS", required_keys=["INFERENCE_AGENTS_TOKEN"])]
)


@app.function(volumes={MODELS_DIR: volume}, timeout=4 * HOURS)
def download_model(model_name, force_download=False):
    from huggingface_hub import snapshot_download

    volume.reload()

    snapshot_download(
        model_name,
        local_dir=MODELS_DIR + "/OPHTHAL-AGENT-8B",
        ignore_patterns=[
            "*.pt",
            "*.bin",
            "*.pth",
            "original/*",
        ],  # Ensure safetensors
        force_download=force_download,
        token=os.getenv('INFERENCE_AGENTS_TOKEN'),
    )

    volume.commit()


@app.local_entrypoint()
def main(
    model_name: str = DEFAULT_NAME,
    force_download: bool = False,
):
    download_model.remote(model_name, force_download)
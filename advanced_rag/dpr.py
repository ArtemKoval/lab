import time
import logging
from transformers import (
    DPRQuestionEncoder,
    DPRContextEncoder,
    DPRQuestionEncoderTokenizer,
    DPRContextEncoderTokenizer,
)
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model_and_tokenizer(model_name, model_class, tokenizer_class):
    try:
        logger.info(f"Loading model and tokenizer: {model_name}")
        model = model_class.from_pretrained(model_name)
        tokenizer = tokenizer_class.from_pretrained(model_name)
        return model, tokenizer
    except Exception as e:
        logger.error(f"Error loading model/tokenizer {model_name}: {e}")
        raise


def encode_texts(texts, model, tokenizer, batch_size=4, device='cpu'):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings.append(outputs.pooler_output.cpu())
    return torch.cat(embeddings, dim=0)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    start_time = time.time()

    # Load models and tokenizers
    qe_model, qe_tokenizer = load_model_and_tokenizer(
        "facebook/dpr-question_encoder-single-nq-base",
        DPRQuestionEncoder,
        DPRQuestionEncoderTokenizer
    )
    ce_model, ce_tokenizer = load_model_and_tokenizer(
        "facebook/dpr-ctx_encoder-single-nq-base",
        DPRContextEncoder,
        DPRContextEncoderTokenizer
    )
    qe_model.to(device)
    ce_model.to(device)

    # Encode the query
    query = "Who is Darth Vader?"
    logger.info(f"Encoding query: '{query}'")
    query_inputs = qe_tokenizer(query, return_tensors="pt", truncation=True).to(device)
    with torch.no_grad():
        query_embedding = qe_model(**query_inputs).pooler_output.cpu()

    # Passages
    # Passages from Star Wars lore
    passages = [
        "Tatooine is a desert planet in the Outer Rim Territories and the childhood home of Anakin Skywalker.",
        "The Death Star was a moon-sized space station armed with a planet-destroying superlaser, constructed by the Galactic Empire.",
        "Yoda was a legendary Jedi Master who trained Jedi for over 800 years and played a key role in the Clone Wars.",
        "The Force is an energy field created by all living things, binding the galaxy together, and wielded by both Jedi and Sith.",
        "Darth Vader, once known as Anakin Skywalker, was a Jedi Knight who turned to the dark side and became a Sith Lord.",
        "The Millennium Falcon is a modified YT-1300 Corellian freighter, piloted by Han Solo and Chewbacca.",
        "Order 66 was a directive given by Emperor Palpatine, leading to the mass extermination of the Jedi Order.",
        "The Mandalorian follows a lone bounty hunter in the outer reaches of the galaxy, far from the authority of the New Republic.",
    ]

    # Encode passages
    logger.info("Encoding passages...")
    context_embeddings = encode_texts(passages, ce_model, ce_tokenizer, device=device)

    # Compute similarities
    logger.info("Computing cosine similarities...")
    similarities = cosine_similarity(query_embedding.numpy(), context_embeddings.numpy())
    most_relevant_idx = np.argmax(similarities)
    elapsed = time.time() - start_time

    # Results
    logger.info(f"Most relevant passage: '{passages[most_relevant_idx]}'")
    logger.info(f"Similarity score: {similarities[0][most_relevant_idx]:.4f}")
    logger.info(f"Total time taken: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()

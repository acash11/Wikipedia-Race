from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def cos_sim(goal, hyper, tokenizer, model, device):
    # Sentences we want sentence embeddings for
    sentences = [goal, hyper]         

    # Tokenize sentences
    encoded_input = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt').to(device)

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

    print("Sentence embeddings (", goal, " & ", hyper, "):")
    print(sentence_embeddings)

    emb1 = sentence_embeddings[0].unsqueeze(0)  # shape: [1, d]
    emb2 = sentence_embeddings[1].unsqueeze(0)  # shape: [1, d]

    cos_sim = F.cosine_similarity(emb1, emb2).item()
    print("Cosine similarity:", cos_sim)
    return cos_sim
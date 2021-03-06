"""
Script to get word-embeddings out of Bert-family Models.

Word-embeddings from bert-base-uncasedfor the Lava datset
will be written to ``PATH_TO_BERT_WORD_EMBEDDINGS_FILE`` as a numpy array.

Mapping of vocabulary to index will be stored as JSON at ``PATH_TO_LAVA_VOCAB``


Load the file with:

```
import numpy as np
from alternationprober.constants import PATH_TO_BERT_WORD_EMBEDDINGS_FILE

embeddings = np.load(PATH_TO_BERT_WORD_EMBEDDINGS_FILE, allow_pickle=True))
```

:author: James V. Bruno
:date: 4/30/2022
"""
import json
import numpy as np
import pandas as pd
from transformers import BertTokenizer, BertModel
from torch.nn.modules import Embedding
from torch import Tensor

from alternationprober.constants import (
    PATH_TO_BERT_WORD_EMBEDDINGS_FILE,
    PATH_TO_LAVA_FILE,
    PATH_TO_LAVA_VOCAB,
)


def get_word_embeddings(
    verb: str, embeddings: Embedding, tokenizer: BertTokenizer
) -> Tensor:
    """Return the embedding vector for ``verb``.

    If the tokenizer gives us sub-word pieces, we take the average of the
    embeddings for all the word-pieces, otherwise, we just return the vector.

    Parameters
    ----------
    verb : str
        Verb, as from the LAVA dataset.
    embeddings : Embedding
        The vocab_size x n_dimension embedding layer for the model.
    tokenizer : BertTokenizer
        The tokenizer for the model.

    Returns
    -------
    word_embedding : Tensor
        an 1 x n_dimension Tensor with the word-embeddings for ``verb``.
    """
    inputs = tokenizer(verb, add_special_tokens=False)
    input_ids = inputs["input_ids"]

    # Sometimes we'll have sub-word tokenization, in which case we need
    # to take the mean of the embeddings.  But even if we don't have sub-word
    # tokenization, there's only one embedding in that case, so it's still
    # save to take the mean:
    word_embedding = embeddings.weight[input_ids].mean(axis=0)

    return word_embedding


def main():
    """
    Extract word-level embeddings from the lava dataset using ``bert-base-uncased``.
    """
    try:
        data_df = pd.read_csv(PATH_TO_LAVA_FILE)
    except FileNotFoundError as e:
        message = f"{PATH_TO_LAVA_FILE} not found.  Execute 'sh ./download-datasets.sh' before continuing."
        raise FileNotFoundError(message) from e

    PATH_TO_BERT_WORD_EMBEDDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    model = BertModel.from_pretrained("bert-base-uncased")
    embedding_layer = model.get_input_embeddings()
    tokenizer = tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    # We will output an 2d np.array with the same indices as the lava dataset.
    list_of_output_arrays = []

    # Help keep track of the vocabulary
    lava_vocabulary_to_index = {}

    print("getting word embeddings...")

    for index, row in data_df.iterrows():
        verb = row["verb"]
        word_embedding = get_word_embeddings(verb, embedding_layer, tokenizer)

        lava_vocabulary_to_index[verb] = index

        # convert the word_embedding tensor to a numpy array and add it to the output list.
        list_of_output_arrays.append(word_embedding.detach().numpy())

    np_output_array = np.array(list_of_output_arrays)
    np_output_array.dump(PATH_TO_BERT_WORD_EMBEDDINGS_FILE)

    with PATH_TO_LAVA_VOCAB.open("w") as f:
        json.dump(lava_vocabulary_to_index, f, indent=4, sort_keys=True)

    print(f"Word embeddings file created at {PATH_TO_BERT_WORD_EMBEDDINGS_FILE}.")
    print(f"Vocabulary mapping file crated at {PATH_TO_LAVA_VOCAB}.")


if __name__ == "__main__":
    main()

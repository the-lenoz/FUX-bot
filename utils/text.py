def split_long_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Splits a long message string into a list of smaller strings,
    suitable for sending as multiple Telegram messages.

    Prioritizes splitting by newlines, then by spaces, and finally by brute force
    if individual "words" are too long.

    Args:
        text: The long message string to split.
        max_length: The maximum length for each message chunk.
                    Defaults to 4096 for plain text messages.
                    For captions, use 1024.

    Returns:
        A list of strings, where each string is no longer than max_length.
    """
    if not text:
        return [""]

    messages = []
    current_chunk = []
    current_chunk_length = 0

    # 1. Try to split by newlines first
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        # Check if adding this paragraph (and a potential newline) exceeds the limit
        if current_chunk_length + len(paragraph) + (1 if current_chunk else 0) > max_length:
            if current_chunk:
                messages.append("\n".join(current_chunk))
                current_chunk = []
                current_chunk_length = 0

            # If a single paragraph is too long, it needs further splitting
            if len(paragraph) > max_length:
                sub_chunks = split_by_words_and_force_cut(paragraph, max_length)
                messages.extend(sub_chunks)
            else:
                current_chunk.append(paragraph)
                current_chunk_length += len(paragraph)
        else:
            current_chunk.append(paragraph)
            current_chunk_length += len(paragraph) + (1 if current_chunk else 0) # Account for newline

    if current_chunk:
        messages.append("\n".join(current_chunk))

    # Final check and refinement, especially for chunks created by force-cutting or very long initial paragraphs
    final_messages = []
    for msg in messages:
        if len(msg) > max_length:
            final_messages.extend(split_by_words_and_force_cut(msg, max_length))
        else:
            final_messages.append(msg)

    return final_messages


def split_by_words_and_force_cut(text: str, max_length: int) -> list[str]:
    """
    Helper function to split text by words or force-cut if words are too long.
    """
    chunks = []
    words = text.split(' ')
    current_chunk_words = []
    current_length = 0

    for word in words:
        # If adding the current word (and a space) exceeds max_length
        if current_length + len(word) + (1 if current_chunk_words else 0) > max_length:
            if current_chunk_words:
                chunks.append(" ".join(current_chunk_words))
                current_chunk_words = []
                current_length = 0

            # If a single word is too long, force cut it
            if len(word) > max_length:
                for i in range(0, len(word), max_length):
                    chunks.append(word[i:i + max_length])
            else:
                current_chunk_words.append(word)
                current_length += len(word)
        else:
            current_chunk_words.append(word)
            current_length += len(word) + (1 if current_chunk_words else 0) # Account for space

    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))

    return chunks
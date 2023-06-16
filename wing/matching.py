from wing.models import BookContent, Translation


async def match_book_contents(
    translation: Translation,
    book_content_list: list[tuple[int, BookContent]],
    list_str: str,
) -> None:
    """
    Match chosen book sentences content to this translation
    """
    chosen_bcs = [int(nr) for nr in list_str.split(',')] if list_str else []
    for nr, bc in book_content_list:
        if nr in chosen_bcs:
            if translation.book_contents is None:
                translation.book_contents = [bc.id]
            else:
                translation.book_contents.append(bc.id)
    await translation.save()

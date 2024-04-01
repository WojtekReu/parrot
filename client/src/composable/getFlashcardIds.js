import { ref } from 'vue'

const getFlashcardIds = (bookId) => {
  const book = ref(null)
  const flashcards = ref(null)
  const error = ref(null)

  const load = async () => {
    try {
      let data = await fetch(`http://localhost:8000/api/v1/book/${bookId}`)
      if (!data.ok) {
        throw Error('ERROR: no book available')
      }
      book.value = await data.json()
    }
    catch (err) {
      error.value = err.message
    }
    if (!error.value) {
      try {
        let data2 = await fetch(`http://localhost:8000/api/v1/flashcard/book/${bookId}`)
        if (!data2.ok) {
          throw Error('ERROR: no flashcards available')
        }
        flashcards.value = await data2.json()
      }
      catch (err) {
        error.value = err.message
      }
    }
  }

  return { book, flashcards, error, load }
}

export default getFlashcardIds

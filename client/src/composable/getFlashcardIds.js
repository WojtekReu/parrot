import { ref } from 'vue'

const getFlashcardIds = (bookId) => {
  const book = ref(null)
  const flashcards = ref(null)
  const error = ref(null)

  const load = async () => {
    await fetch(`${process.env.VUE_APP_API_URL}/books/${bookId}`)
      .then(response => response.json())
      .then(data => book.value = data)
      .catch(err => error.value = err.message)
    await fetch(`${process.env.VUE_APP_API_URL}/books/${bookId}/flashcards`)
    .then(response => response.json())
    .then(data => flashcards.value = data)
    .catch(err => error.value = err.message)
  }

  return { book, flashcards, error, load }
}

export default getFlashcardIds

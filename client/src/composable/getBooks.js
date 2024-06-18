import { ref } from 'vue'

const getBooks = () => {
  const books = ref([])
  const error = ref(null)

  const load = async () => {
    await fetch(`${process.env.VUE_APP_API_URL}/books/all`)
      .then(response => response.json())
      .then(data => books.value = data)
      .catch(err => error.value = err.message)
  }

  return { books, error, load }
}

export default getBooks

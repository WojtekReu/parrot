import { ref } from 'vue'

const getBooks = () => {
    const books = ref([])
    const error = ref(null)

    const load = async () => {
        try {
          let data = await fetch('http://localhost:8000/api/v2/books/all')
          if (!data.ok) {
            throw Error('ERROR: no books available')
          }
          books.value = await data.json()
        }
        catch (err) {
          error.value = err.message
        }
    }

    return { books, error, load }
}

export default getBooks

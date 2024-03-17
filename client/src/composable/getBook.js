import { ref } from 'vue'

const getBook = (id) => {
    const book = ref(null)
    const error = ref(null)

    const load = async () => {
        try {
          let data = await fetch('http://localhost:8000/book/' + id)
          if (!data.ok) {
            throw Error('ERROR: no books available')
          }
          book.value = await data.json()
        }
        catch (err) {
          error.value = err.message
        }
    }

    return { book, error, load }
}

export default getBook

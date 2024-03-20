<template>
  <h1>Books</h1>
  <div v-if="error">
    {{ error }}
  </div>
  <table class="book-list">
    <tr>
      <th>ID</th>
      <th>Title</th>
      <th>Author</th>
      <th>Sentences</th>
      <th>Words</th>
    </tr>
    <tr v-for="book in books" :key="book.id">
      <Book :book="book" />
    </tr>
  </table>
</template>

<script>
import getBooks from '@/composable/getBooks'
import Book from '@/components/book/Element'

export default {
  name: 'books',
  components: { Book },
  setup() {
    const { books, error, load } = getBooks()
    
    load()

    return { books, error }
  }
}
</script>

<style>
.book-list {
  margin: 0 auto;
}
</style>
<template>
  <td>{{ book.id }}</td>
  <td><router-link :to="{ name: 'book', params: { id: book.id }}">{{ book.title }}</router-link></td>
  <td>{{ book.author }}</td>
  <td>{{ book.sentences_count }}</td>
  <td>{{ book.words_count }}</td>
</template>

<script>
export default {
    props: ['book'],
}
</script>
<template>
  <div v-if="error">{{ error }}</div>
  Words list
  <input type="text" v-model="wordsFilter" @keyup="searchWords()">
  <input type="button" value="clear" @click="clear">
  <ol>
    <li v-for="word in wordsList" :key="word.id" class="word-element">
      {{ word.lem }}, {{ word.pos }}, {{ word.synset }}, {{ word.declination }} - {{ word.definition }}
    </li>
  </ol>
</template>

<script>
export default {
  name: 'WordsList',
  data() {
    return {
      error: '',
      wordsFilter: '',
      wordsList: []
    }
  },
  methods: {
    clear() {
      this.wordsFilter = ''
    },
    async searchWords() {
      if (this.wordsFilter) {
        await fetch(`${process.env.VUE_APP_API_URL}/words/find/${this.wordsFilter}`)
          .then(response => response.json())
          .then(data => this.wordsList = data)
          .catch(err => this.error = err.message)
      }
    }
  }
}
</script>

<style>
.word-element {
  text-align: left;
}
</style>
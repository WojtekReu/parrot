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
        try {
          let response = await fetch(
            `http://localhost:8000/api/v2/words/find/${this.wordsFilter}`
          )
          if (!response.ok) {
            throw Error('ERROR: API result error for word find request')
          }
          let data = await response.json()
          this.wordsList = data
        } catch (err) {
          this.error = err.message
        }
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
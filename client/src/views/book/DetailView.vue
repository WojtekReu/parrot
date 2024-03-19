<template>
    <div v-if="error">{{ error }}</div>
    <div v-if="book">
        <h1>{{ book.title }} - {{ book.author }}</h1>
    </div>
    <p>nr: <input type="text" class="flashcardNr" v-model="flashcardNr"></p>
    <div v-if="flashcardNr">
        <div v-if="error2">{{ error2 }}</div>
        <div v-else-if="!status">Loading...</div>
        <div v-else-if="!flashcard">Translation didn't find</div>
        <div v-else>
            <div v-if="sentences">
                <ol class="sentences">
                    <li v-for="sentence in sentences" :key="id">
                        (nr: {{ sentence.nr }}) -
                        {{ sentence.sentence }}
                    </li>
                </ol>
            </div>
            <p><span class="description">Przetłumacz:</span> {{ flashcard.key_word }}</p>
            <p>
                <input type="text" v-focus v-model="typedText" @keypress="ready">
            </p>
        </div>
        <div v-if="yourAnswer">
            <p class="correct" v-if="flashcard.translations.includes(yourAnswer)">
                {{ source }} -> {{ yourAnswer }}
            </p>
            <div v-else>
                <p class="incorrect">{{ yourAnswer }}</p>
                <div v-for="translation in flashcard.translations">{{ translation }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import getFlashcardIds from '@/composable/getFlashcardIds'

const focus = {
  mounted: (el) => el.focus()
}

export default {
    props: ['id'],
    name: 'BookView',
    setup(props) {
        const { book, flashcards, error, load } = getFlashcardIds(props.id)
        load()

        return { book, flashcards, error }
    },
    directives: {
        // enables v-focus in template
        focus
    },
    data() {
        return {
            status: null,
            flashcardNr: '',
            flashcard: null,
            error2: null,
            typedText: '',
            yourAnswer: '',
            rightAnswer: '',
            source: '',
            sentences: [],
        }
    },
    methods: {
        async fetchData() {
            this.status = null
            if (this.flashcardNr) {
                let fValues = this.flashcards[this.flashcardNr]
                this.error2 = null
                try {
                    let response = await fetch(
                        `http://localhost:8000/flashcard/${fValues.flashcard_id}`
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for flashcard request')
                    }
                    this.flashcard = await response.json()
                    if (this.flashcard) {
                        this.sentences = []
                        for (const sentence_id of fValues.sentence_ids) {
                            response = await fetch(
                                `http://localhost:8000/sentence/${sentence_id}`
                            )
                            if (!response.ok) {
                                throw Error('ERROR: API result error for sentece request')
                            }
                            let res = await response.json()
                            if (res.nr !== 0) {
                                this.sentences.push(res)
                            }
                        }
                    }
                    this.status = 'ready'
                } catch (err) {
                    this.error2 = err.message
                }
            }
        },
        ready(keyboardEvent) {
            if (keyboardEvent.key === 'Enter') {
                this.source = this.flashcard.key_word
                this.rightAnswer = this.flashcard.translations
                this.yourAnswer = this.typedText
                if (this.yourAnswer === '') {
                    this.getNextTranslation()
                } else {
                    this.yourAnswer = this.typedText
                }
                this.typedText = ''
            } else if (this.yourAnswer) {
                this.yourAnswer = ''
            }
        },
        getNextTranslation() {
            this.flashcardNr ++
        }
    },
    mounted() {
        this.fetchData()
    },
    watch: {
        flashcardNr() {
            this.fetchData()
        }
    }
}
</script>

<style>
.correct {
    color: green;
}
.incorrect {
    color: crimson;
}
.flashcardNr {
    width: 22px;
    text-align: center;
}
ol.sentences {
    text-align: left;
}
</style>
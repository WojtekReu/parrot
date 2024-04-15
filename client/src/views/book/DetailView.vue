<template>
    <div v-if="error">{{ error }}</div>
    <div v-if="book">
        <h3>{{ book.title }} - {{ book.author }}</h3>
    </div>
    <p>flashcard nr: <input type="text" class="flashcardNr" v-model="flashcardNr"><input type="button" @click="getNextTranslation" value="Next"></p>
    <div>Your results: <span class="correct">{{ correctResults }}</span> / {{ totalResults }}</div>
    <div v-if="flashcardNr" class="flashcard">
        <div v-if="error"></div>
        <div v-else-if="!status">Loading...</div>
        <div v-else>
            <div v-if="sentences">
                <ol class="sentences">
                    <li v-for="sentence in sentences" :key="id">
                        {{ sentence.sentence }}
                    </li>
                </ol>
            </div>
            <p>
                <span class="label">EN: </span> {{ flashcard.keyword }}
            </p>
            <p>
                <span class="label">PL: </span>
                <input type="text" v-focus v-model="typedText" @keypress="ready">
            </p>
            <div v-if="yourAnswer">
                <p class="correct" v-if="flashcard.translations.includes(yourAnswer)">
                    <span class="label">Correct! </span> {{ yourAnswer }}
                </p>
                <div v-else>
                    <div class="incorrect"><span class="label">Your:</span>{{ yourAnswer }}</div>
                    <div v-for="translation in flashcard.translations"><span class="label">Should be:</span>{{ translation }}</div>
                </div>
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
            correctResults: 0,
            totalResults: 0,
            status: null,
            flashcardNr: '',
            flashcard: null,
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
            this.yourAnswer = ''
            let flashcardId = ''
            if (this.flashcardNr) {
                flashcardId = this.flashcards[this.flashcardNr]
            }
            if (flashcardId !== '' && flashcardId) {
                this.error = null
                try {
                    let response = await fetch(
                        `http://localhost:8000/api/v1/flashcard/${flashcardId}`
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for flashcard request')
                    }
                    this.flashcard = await response.json()
                    if (this.flashcard) {
                        this.sentences = []
                        response = await fetch(
                            `http://localhost:8000/api/v1/sentence/book/${this.book.id}/${flashcardId}`
                        )
                        if (!response.ok) {
                            throw Error('ERROR: API result error for sentence request')
                        }
                        this.sentences = await response.json()
                    }
                    this.status = 'ready'
                } catch (err) {
                    this.error = err.message
                }
            }
        },
        ready(keyboardEvent) {
            if (keyboardEvent.key === 'Enter') {
                this.source = this.flashcard.keyword
                this.rightAnswer = this.flashcard.translations
                this.yourAnswer = this.typedText
                if (this.yourAnswer === '') {
                    this.getNextTranslation()
                } else {
                    if (this.rightAnswer.includes(this.yourAnswer)) {
                        this.correctResults ++
                    }
                    this.totalResults ++
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
    width: 30px;
    text-align: center;
}
.flashcard {
    max-width: 650px;
    text-align: left;
    margin: 0 auto;
}
.label {
    display: inline-block;
    width: 70px;
    font-size: small;
    text-align: right;
    margin-right: 10px;
}
ol.sentences {
    max-height: 200px;
    overflow-x: hidden;
    overflow-y: auto;
}
</style>
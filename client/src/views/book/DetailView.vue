<template>
    <div v-if="error">{{ error }}</div>
    <div v-if="book">
        <h3>{{ book.title }} - {{ book.author }}</h3>
    </div>
    <p>flashcard nr: <input type="text" class="flashcardNr" v-model="flashcardNr"><input type="button" @click="getNextTranslation" value="Next"></p>
    <div v-if="flashcardNr">
        <div v-if="error2">{{ error2 }}</div>
        <div v-else-if="!status">Loading...</div>
        <div v-else-if="!flashcard">Translation didn't find</div>
        <div v-else>
            <div v-if="sentences">
                <ol class="sentences">
                    <li v-for="sentence in sentences" :key="id">
                        {{ sentence.sentence }}
                    </li>
                </ol>
            </div>
            <p><span class="description">EN:</span> {{ flashcard.keyword }}</p>
            <p>
                PL: <input type="text" v-focus v-model="typedText" @keypress="ready">
            </p>
            <div v-if="yourAnswer">
                <p class="correct" v-if="flashcard.translations.includes(yourAnswer)">
                    {{ source }} -> {{ yourAnswer }}
                </p>
                <div v-else>
                    <div class="incorrect">{{ yourAnswer }}</div>
                    <div v-for="translation in flashcard.translations">{{ translation }}</div>
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
            this.yourAnswer = ''
            if (this.flashcardNr) {
                let flashcardId = this.flashcards[this.flashcardNr]
                this.error2 = null
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
                    this.error2 = err.message
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
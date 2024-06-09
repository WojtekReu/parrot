<template>
    <div v-if="error">{{ error }}</div>
    <div v-if="book">
        <h3>{{ book.title }} - {{ book.author }}</h3>
    </div>
    <p>
        flashcard nr: 
        <input type="text" class="flashcardNr" v-model="flashcardNr" @keypress="getNextFlashcard">
        <input type="hidden" v-model="flashcardNrHidden">
        <input type="button" @click="getNextTranslation" value="Next">
    </p>
    <div>Your results: <span class="correct">{{ correctResults }}</span> / {{ totalResults }}</div>
    <div v-if="flashcardNrHidden" class="flashcard">
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
            <input type="button" @click="editFlashcard" value="Edit">
            <input type="button" @click="showDefinition" value="Show">
            <div v-if="words.length > 0">
                <ul>
                    <li v-for="w1 in words" :key="id">{{ w1.lem }} - {{ w1.synset }} - {{ w1.definition }}</li>
                </ul>
            </div>
            <div v-if="showEditFlashcard">
                <form @submit="saveChanges">
                    <ol class="sentences">
                        <li v-for="sentence in sentences" :key="id">
                            <input type="button" @click="getWordDefinition(sentence.id)" value="Check"><input type="checkbox" checked="true" name="sentence[]" :value="sentence.id"> {{ sentence.sentence.slice(0, 70) }}
                        </li>
                    </ol>
                    <div v-if="word">word.lem = {{ word.lem }}</div>
                    <div v-if="synsets.length">
                        <ol>
                            <li v-for="synset in synsets">
                                <input type="radio" :checked="synset[0]" name="synset" :value="synset[1]"> {{ synset[1] }} - {{ synset[2] }}
                            </li>
                        </ol>
                        <div>
                            <input type="submit" @click="saveChanges()" value="Save">
                            <input type="button" @click="cancelChanges()" value="Cancel">
                        </div>
                    </div>
                </form>
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
            flashcardNrHidden: '',
            flashcard: null,
            typedText: '',
            yourAnswer: '',
            rightAnswer: '',
            source: '',
            sentences: [],
            showEditFlashcard: false,
            word: null,
            synsets: [],
            sentenceCheckbox: '',
            words: [],
        }
    },
    methods: {
        async fetchData() {
            this.status = null
            this.yourAnswer = ''
            let flashcardId = ''
            if (this.flashcardNrHidden) {
                flashcardId = this.flashcards[this.flashcardNrHidden]
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
        getNextFlashcard(keyboardEvent) {
            if (keyboardEvent.key === 'Enter') {
                this.flashcardNrHidden = this.flashcardNr
            }
        },
        getNextTranslation() {
            this.flashcardNr ++
            this.flashcardNrHidden = this.flashcardNr
            this.showEditFlashcard = false
            this.word = null
            this.synsets = []
            this.words = []
        },
        async editFlashcard() {
            this.showEditFlashcard = true
        },
        async showDefinition() {
            try {
                let response = await fetch(
                    `http://localhost:8000/api/v1/word/find-words/${this.flashcard.id}`
                )
                if (!response.ok) {
                    throw Error('ERROR: API result error for find-words request')
                }
                this.words = await response.json()
            } catch (err) {
                this.error = err.message
            }
        },
        async getWordDefinition(sentence_id) {
            try {
                let response = await fetch(
                    `http://localhost:8000/api/v1/word/find-synset/${this.flashcard.id}/${sentence_id}`
                )
                if (!response.ok) {
                    throw Error('ERROR: API result error for word-match request')
                }
                let response_json = await response.json()
                this.word = response_json.word
                this.synsets = response_json.synsets
            } catch (err) {
                this.error = err.message
            }
        },
        async saveChanges(submitEvent) {
            if (submitEvent) {
                submitEvent.preventDefault()
                let sentence_ids = []
                let disconnect_ids = []
                let sentencesList = submitEvent.target.elements["sentence[]"]
                if (sentencesList.value) {
                    if (sentencesList.type === "checkbox" && sentencesList.checked === true) {
                        sentence_ids.push(sentencesList.value)
                    } else {
                        disconnect_ids.push(sentence_ids.value)
                    }
                } else {
                    submitEvent.target.elements["sentence[]"].forEach((el) => {
                        if (el.type === "checkbox" && el.checked === true) {
                            sentence_ids.push(el.value)
                        } else {
                            disconnect_ids.push(el.value)
                        }
                    })
                }
                this.word.synset = submitEvent.target.elements.synset.value
                this.synsets.forEach((el) => {
                    if (el[1] === this.word.synset) {
                        this.word.definition = el[2]
                    }
                })
                let data = this.word
                let wordId = this.word.id
                delete data.id
                console.log(data)
                const requestOptions = {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                }
                try {
                    let response = await fetch(
                        `http://localhost:8000/api/v1/word/update/${wordId}`, requestOptions
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for word-match-save request')
                    }
                    let response_json = await response.json()
                } catch (err) {
                    this.error = err.message
                }
                let data2 = {
                    "word_id": wordId,
                    "disconnect_ids": disconnect_ids,
                    "sentence_ids": sentence_ids,
                }
                const requestOptions2 = {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data2),
                }
                try {
                    let response = await fetch(
                        `http://localhost:8000/api/v1/word/match-word-sentences/${wordId}`, requestOptions2
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for match-word-sentences request')
                    }
                } catch (err) {
                    this.error = err.message
                }

                let data3 = {
                    "flashcard_id": this.flashcards.id,
                    "disconnect_ids": disconnect_ids,
                    "sentence_ids": sentence_ids,
                }
                const requestOptions3 = {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data3),
                }
                try {
                    let response = await fetch(
                        `http://localhost:8000/api/v1/flashcard/match-flashcard-sentences/${this.flashcard.id}`, requestOptions3
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for match-flashcard-sentences request')
                    }
                } catch (err) {
                    this.error = err.message
                }
            }

        },
        cancelChanges() {
            this.showEditFlashcard = false
            this.word = null
            this.synsets = []
        },
    },
    mounted() {
        this.fetchData()
    },
    watch: {
        flashcardNrHidden() {
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
<template>
    <div v-if="error">{{ error }}</div>
    <div v-if="book">
        <h1>{{ book.title }} - {{ book.author }}</h1>
    </div>
    <p><input type="text" class="translationId" v-model="translationId"></p>
    <div v-if="translationId">
        <div v-if="error2">{{ error2 }}</div>
        <div v-else-if="!status">Loading...</div>
        <div v-else-if="!translation">Translation didn't find</div>
        <div v-else>
            <div v-if="sentences.sentences.length">
                <p v-for="row in sentences.sentences.slice(0,3)" :key="row.id">{{ row.sentence }}</p>
            </div>
            <p><span class="description">Przetłumacz:</span> {{ translation.source }}</p>
            <p>
                <input type="text" v-model="typedText" @keypress="ready">
            </p>
        </div>
        <div v-if="yourAnswer">
            <p class="correct" v-if="yourAnswer === rightAnswer">
                {{ yourAnswer }}: {{ source }}
            </p>
            <div v-else>
                <p class="incorrect">{{ yourAnswer }}</p>
                <p>{{ translation.text }}</p>
            </div>
        </div>
    </div>
</template>

<script>
import getBook from '@/composable/getBook'

export default {
    props: ['id'],
    name: 'BookView',
    setup(props) {
        const { book, error, load } = getBook(props.id)
        load()

        return { book, error }
    },
    data() {
        return {
            status: null,
            translationId: '1',
            translation: null,
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
            if (this.translationId) {
                this.error2 = null
                try {
                    let response = await fetch(
                        `http://localhost:8000/translations_by_book/${this.id}/${this.translationId}`
                    )
                    if (!response.ok) {
                        throw Error('ERROR: API result error for translation request')
                    }
                    this.translation = await response.json()
                    if (this.translation) {
                        response = await fetch(
                            `http://localhost:8000/fetch_sentences/${this.id}/${this.translation.bword_id}`
                        )
                        if (!response.ok) {
                            throw Error('ERROR: API result error for fetch_senteces request')
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
                this.source = this.translation.source
                this.rightAnswer = this.translation.text
                this.yourAnswer = this.typedText
                if (this.yourAnswer === this.rightAnswer) {
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
            this.translationId ++
        }
    },
    mounted() {
        this.fetchData()
    },
    watch: {
        translationId() {
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
.translationId {
    width: 22px;
    text-align: center;
}
</style>
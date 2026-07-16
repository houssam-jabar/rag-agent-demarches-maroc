import { useState, useRef, useEffect } from 'react'
import './ChatWidget.css'

const API_URL = 'http://127.0.0.1:8000/chat'
const MARQUEUR_SOURCES = '<<<SOURCES>>>'

const SUGGESTIONS = [
  'Documents pour un acte de naissance ?',
  'Comment se marier au Maroc ?',
  "Prix d'un extrait de casier judiciaire ?",
]

function ChatWidget() {
  const [ouvert, setOuvert] = useState(false)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [chargement, setChargement] = useState(false)
  const finDesMessages = useRef(null)

  useEffect(() => {
    finDesMessages.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chargement])

  async function envoyer(texte) {
    if (!texte.trim() || chargement) return
    const historiqueMaj = [...messages, { role: 'user', texte }]
    setMessages([...historiqueMaj, { role: 'bot', texte: '', sources: [] }])
    setQuestion('')
    setChargement(true)

    let texteCible = ''
    let sourcesFinales = []
    let reseauTermine = false

    const minuteur = setInterval(() => {
      setMessages((prev) => {
        const copie = [...prev]
        const dernier = copie[copie.length - 1]

        if (dernier.texte.length < texteCible.length) {
          copie[copie.length - 1] = { ...dernier, texte: texteCible.slice(0, dernier.texte.length + 1) }
          return copie
        }

        if (reseauTermine) {
          clearInterval(minuteur)
          setChargement(false)
          if (sourcesFinales.length > 0) {
            copie[copie.length - 1] = { ...dernier, sources: sourcesFinales }
            return copie
          }
        }
        return prev
      })
    }, 15)

    try {
      const reponseHttp = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: historiqueMaj, top_k: 5 }),
      })
      if (!reponseHttp.ok || !reponseHttp.body) throw new Error(`code ${reponseHttp.status}`)

      const lecteur = reponseHttp.body.getReader()
      const decodeur = new TextDecoder('utf-8')
      let brut = ''

      while (true) {
        const { done, value } = await lecteur.read()
        if (done) break
        brut += decodeur.decode(value, { stream: true })
        const indexMarqueur = brut.indexOf(MARQUEUR_SOURCES)
        texteCible = indexMarqueur === -1 ? brut : brut.slice(0, indexMarqueur)
      }

      const indexMarqueur = brut.indexOf(MARQUEUR_SOURCES)
      if (indexMarqueur !== -1) {
        texteCible = brut.slice(0, indexMarqueur).trimEnd()
        try {
          sourcesFinales = JSON.parse(brut.slice(indexMarqueur + MARQUEUR_SOURCES.length))
        } catch {
          sourcesFinales = []
        }
      } else {
        texteCible = brut.trimEnd()
      }
    } catch (erreur) {
      texteCible = 'Une erreur est survenue, reessayez dans un instant.'
    } finally {
      reseauTermine = true
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    envoyer(question)
  }

  return (
    <div className="dm-widget">
      {ouvert && (
        <div className="dm-panel">
          <header className="dm-header">
            <div className="dm-header-identite">
              <span className="dm-avatar" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
                  <path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.6" />
                  <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" />
                  <path d="M8 12.5h8M8 15.5h8M8 9.5h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                </svg>
              </span>
              <div>
                <p className="dm-titre">Assistant État Civil</p>
                <p className="dm-sous-titre">Démarches Maroc</p>
              </div>
            </div>
            <button className="dm-fermer" onClick={() => setOuvert(false)} aria-label="Fermer la fenetre de chat">×</button>
          </header>

          <div className="dm-corps">
            {messages.length === 0 && (
              <div className="dm-accueil">
                <p>Bonjour. Posez-moi une question sur l'état civil : acte de naissance, mariage, décès, livret de famille...</p>
                <div className="dm-suggestions">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} type="button" onClick={() => envoyer(s)}>{s}</button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => {
              const estDernier = i === messages.length - 1
              const enAttente = estDernier && m.role === 'bot' && chargement && !m.texte

              return (
                <div key={i} className={`dm-message dm-${m.role}`}>
                  {enAttente ? (
                    <div className="dm-frappe" aria-label="Le chatbot ecrit">
                      <span></span><span></span><span></span>
                    </div>
                  ) : (
                    <p>{m.texte}</p>
                  )}
                </div>
              )
            })}
            <div ref={finDesMessages} />
          </div>

          <form className="dm-saisie" onSubmit={onSubmit}>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ecrivez votre question..."
              aria-label="Votre question"
            />
            <button type="submit" disabled={chargement} aria-label="Envoyer">
              <svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor">
                <path d="M3 11l18-8-8 18-2.5-7.5L3 11Z" />
              </svg>
            </button>
          </form>
        </div>
      )}

      <button
        className="dm-lanceur"
        onClick={() => setOuvert((v) => !v)}
        aria-label={ouvert ? 'Fermer le chat' : 'Ouvrir le chat'}
      >
        {ouvert ? (
          <span className="dm-lanceur-croix">×</span>
        ) : (
          <svg viewBox="0 0 24 24" width="25" height="25" fill="currentColor">
            <path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-5 4V6a1 1 0 0 1 1-1Z" />
          </svg>
        )}
      </button>
    </div>
  )
}

export default ChatWidget

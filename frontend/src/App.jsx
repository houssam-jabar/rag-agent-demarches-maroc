import ChatWidget from './ChatWidget'
import './App.css'

function App() {
  return (
    <div className="page-hote">
      <div className="page-hote-contenu">
        <p className="page-hote-etiquette">Aperçu — page hôte simulée</p>
        <h1>www.demarchesmaroc.com</h1>
        <p>
          Le widget en bas à droite est le composant à intégrer tel quel sur le vrai site.
          Cette page grise autour ne sert qu'à simuler le contexte d'intégration.
        </p>
      </div>
      <ChatWidget />
    </div>
  )
}

export default App

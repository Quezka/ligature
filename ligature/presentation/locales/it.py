"""Traduzione italiana dell'interfaccia di Ligature."""

NAMES: dict[str, list[str]] = {}

# English singular -> (one, other) forms.
PLURALS = {
    "entity": ("entità", "entità"),
    "relationship": ("relazione", "relazioni"),
    "class": ("classe", "classi"),
    "link": ("collegamento", "collegamenti"),
}

MESSAGES = {
    'Interface size': 'Dimensione dell’interfaccia',
    'Automatic': 'Automatica',
    'Applies after a restart. Automatic makes everything a little smaller on small screens.': 'Si applica dopo il riavvio. La modalità automatica rimpicciolisce un po’ tutto sugli schermi piccoli.',
    # ---- window and pages
    "Ligature": "Ligature",
    "Home": "Home",
    "Diagram": "Diagramma",
    "SQL": "SQL",
    "More": "Altro",
    "Start": "Inizia",
    "Recent": "Recenti",
    "ER and UML class diagrams for school, with the SQL they make.":
        "Diagrammi E/R e diagrammi delle classi UML per la scuola, con l’SQL che ne deriva.",
    "New ER diagram": "Nuovo diagramma E/R",
    "New UML class diagram": "Nuovo diagramma delle classi UML",
    "Entities, relationships, keys → SQL": "Entità, relazioni, chiavi → SQL",
    "Classes, inheritance, associations": "Classi, ereditarietà, associazioni",
    "Open…": "Apri…",
    "A .ligature file, or a picture Ligature made": "Un file .ligature o un’immagine creata da Ligature",
    "Or look around a sample first:": "Oppure dai prima un’occhiata a un esempio:",
    "School register (ER)": "Registro scolastico (E/R)",
    "Geometric shapes (UML)": "Figure geometriche (UML)",
    "Diagrams you open or save show up here.":
        "I diagrammi che apri o salvi compaiono qui.",
    "ER diagram": "Diagramma E/R",
    "UML class diagram": "Diagramma delle classi UML",
    "Not saved yet": "Non ancora salvato",
    "Untitled diagram": "Diagramma senza titolo",
    "saved": "salvato",
    "unsaved changes": "modifiche non salvate",
    "Unsaved changes": "Modifiche non salvate",
    "Save the changes to this diagram first?": "Salvare prima le modifiche a questo diagramma?",

    # ---- files
    "Save": "Salva",
    "Save (Ctrl+S)": "Salva (Ctrl+S)",
    "Save as…": "Salva con nome…",
    "Save the diagram": "Salva il diagramma",
    "Open a diagram": "Apri un diagramma",
    "Open a picture from the clipboard": "Apri un’immagine dagli appunti",
    "Copy a Ligature picture first (e.g. from a note), then try again.":
        "Copia prima un’immagine di Ligature (ad esempio da una nota), poi riprova.",
    "Diagrams": "Diagrammi",
    "All files": "Tutti i file",
    "Ligature diagram": "Diagramma di Ligature",
    "Editable PNG picture": "Immagine PNG modificabile",
    "Editable SVG picture": "Immagine SVG modificabile",
    "Export": "Esporta",
    "PNG picture (editable)…": "Immagine PNG (modificabile)…",
    "SVG picture (editable)…": "Immagine SVG (modificabile)…",
    "PDF…": "PDF…",
    "PNG picture": "Immagine PNG",
    "SVG picture": "Immagine SVG",
    "PDF document": "Documento PDF",
    "Export as PNG…": "Esporta come PNG…",
    "Export as SVG…": "Esporta come SVG…",
    "Export as PDF…": "Esporta come PDF…",
    "Copy as picture": "Copia come immagine",
    "Copy as picture (paste it into notes)": "Copia come immagine (incollala nelle note)",
    "Exported pictures are always drawn on white.":
        "Le immagini esportate hanno sempre lo sfondo bianco.",

    # ---- tools
    "Select and move": "Seleziona e sposta",
    "Entity": "Entità",
    "Relationship": "Relazione",
    "Class": "Classe",
    "Link": "Collegamento",
    "Click where the entity goes.": "Fai clic dove va l’entità.",
    "Click where the class goes.": "Fai clic dove va la classe.",
    "Click the first entity.": "Fai clic sulla prima entità.",
    "Click the first class.": "Fai clic sulla prima classe.",
    "Now click the second entity (the same one again for a recursive relationship). Esc cancels.":
        "Ora fai clic sulla seconda entità (di nuovo la stessa per una relazione ricorsiva). Esc annulla.",
    "Now click the parent class or interface. Esc cancels.":
        "Ora fai clic sulla classe o interfaccia genitore. Esc annulla.",
    "Now click the second class. Esc cancels.": "Ora fai clic sulla seconda classe. Esc annulla.",
    "Undo (Ctrl+Z)": "Annulla (Ctrl+Z)",
    "Redo (Ctrl+Shift+Z)": "Ripeti (Ctrl+Shift+Z)",
    "Zoom out (Ctrl+-)": "Riduci (Ctrl+-)",
    "Zoom in (Ctrl+=, or Ctrl+scroll)": "Ingrandisci (Ctrl+= o Ctrl+rotellina)",
    "Fit the diagram (Ctrl+0)": "Adatta il diagramma (Ctrl+0)",
    "Fit the diagram": "Adatta il diagramma",
    "Add an entity here": "Aggiungi un’entità qui",
    "Add a class here": "Aggiungi una classe qui",
    "Duplicate": "Duplica",
    "Delete": "Elimina",
    "{count} selected": "{count} selezionati",

    # ---- the panel
    "Title": "Titolo",
    "Notation": "Notazione",
    "Chen": "Chen",
    "Crow's foot": "Zampa di gallina",
    "Double-click empty space to add an entity. To join entities, pick Relationship in the toolbar and click one entity, then the other (the same one twice for a recursive relationship). Drag to move; Delete removes.":
        "Fai doppio clic su uno spazio vuoto per aggiungere un’entità. Per collegare le entità, "
        "scegli Relazione nella barra degli strumenti e fai clic su un’entità, poi sull’altra "
        "(sulla stessa due volte per una relazione ricorsiva). Trascina per spostare; Canc elimina.",
    "Double-click empty space to add a class. To link classes, pick a link type in the toolbar and click one class, then the other: for inheritance, click the child first, then the parent.":
        "Fai doppio clic su uno spazio vuoto per aggiungere una classe. Per collegare le classi, "
        "scegli un tipo di collegamento nella barra degli strumenti e fai clic su una classe, poi "
        "sull’altra: per l’ereditarietà, fai clic prima sulla classe figlia, poi sul genitore.",
    "Entity name": "Nome dell’entità",
    "Weak entity (identified through a relationship)":
        "Entità debole (identificata tramite una relazione)",
    "Attributes": "Attributi",
    "No attributes yet.": "Ancora nessun attributo.",
    "Add attribute": "Aggiungi attributo",
    "name": "nome",
    "Column type in SQL": "Tipo di colonna in SQL",
    "Part of the key (identifier)": "Parte della chiave (identificatore)",
    "Optional: may be left empty": "Facoltativo: può restare vuoto",
    "Remove attribute": "Rimuovi attributo",
    "The key icon marks the identifier (the primary key). “0,1” marks an optional attribute.":
        "L’icona della chiave indica l’identificatore (la chiave primaria). “0,1” indica un attributo facoltativo.",
    "Relationship name": "Nome della relazione",
    "Entities": "Entità",
    "Add an entity": "Aggiungi un’entità",
    "For relationships between three or more entities": "Per relazioni tra tre o più entità",
    "How many times this entity takes part: (min,max)":
        "Quante volte questa entità partecipa: (min,max)",
    "role": "ruolo",
    "Remove this entity from the relationship": "Rimuovi questa entità dalla relazione",
    "(min,max) is how many times each entity takes part: (1,1) exactly once, (0,N) any number of times. A role tells the two sides of a recursive relationship apart.":
        "(min,max) indica quante volte ogni entità partecipa: (1,1) esattamente una volta, "
        "(0,N) un numero qualsiasi di volte. Un ruolo distingue i due lati di una relazione ricorsiva.",
    "Class name": "Nome della classe",
    "Abstract class": "Classe astratta",
    "Interface": "Interfaccia",
    "Enumeration": "Enumerazione",
    "Operations": "Operazioni",
    "- nome: String\n- eta: int": "- nome: String\n- eta: int",
    "+ getNome(): String": "+ getNome(): String",
    "One per line. Start with + public, - private, # protected or ~ package; write “static” or “abstract” before the name to underline it or put it in italics.":
        "Una per riga. Inizia con + public, - private, # protected o ~ package; scrivi “static” o "
        "“abstract” prima del nome per sottolinearlo o metterlo in corsivo.",
    "Type": "Tipo",
    "Association": "Associazione",
    "Directed association": "Associazione orientata",
    "Aggregation": "Aggregazione",
    "Composition": "Composizione",
    "Inheritance (generalisation)": "Ereditarietà (generalizzazione)",
    "Realisation (implements)": "Realizzazione (implements)",
    "Dependency": "Dipendenza",
    "Multiplicity at the start": "Molteplicità all’inizio",
    "Multiplicity at the end": "Molteplicità alla fine",
    "Label": "Etichetta",
    "e.g. contiene": "es. contiene",
    "Reverse direction": "Inverti direzione",

    # ---- SQL
    "The tables your ER diagram becomes, ready to paste into a database.":
        "Le tabelle in cui si trasforma il tuo diagramma E/R, pronte da incollare in un database.",
    "Standard": "Standard",
    "Copy": "Copia",
    "Save as .sql…": "Salva come .sql…",
    "Save the SQL": "Salva l’SQL",
    "SQL script": "Script SQL",
    "Logical schema": "Schema logico",
    "CREATE TABLE statements": "Istruzioni CREATE TABLE",
    "Underlined: primary key. Italics with *: foreign key. ? may be empty.":
        "Sottolineato: chiave primaria. Corsivo con *: chiave esterna. ? può essere vuoto.",
    "SQL comes from ER diagrams. Open or start an ER diagram to see its tables here.":
        "L’SQL deriva dai diagrammi E/R. Apri o crea un diagramma E/R per vederne qui le tabelle.",
    "No entities yet.": "Ancora nessuna entità.",
    "“{subject}” has no key, so an “id” column was added. Mark its identifier with the key icon.":
        "“{subject}” non ha una chiave, quindi è stata aggiunta una colonna “id”. Segna il suo "
        "identificatore con l’icona della chiave.",
    "“{subject}” is weak but no relationship identifies it: give it a (1,1) relationship to its owner.":
        "“{subject}” è debole ma nessuna relazione la identifica: dalle una relazione (1,1) con la "
        "sua entità proprietaria.",
    "“{subject}” is identified through a circle of weak entities.":
        "“{subject}” è identificata tramite un ciclo di entità deboli.",
    "“{subject}” joins fewer than two entities, so it was left out.":
        "“{subject}” collega meno di due entità, quindi è stata omessa.",
    "Two tables are called “{subject}”; one was renamed.":
        "Due tabelle si chiamano “{subject}”; una è stata rinominata.",
    "“{subject}” appears twice; the second was left out.":
        "“{subject}” compare due volte; la seconda è stata omessa.",

    # ---- settings, help, about
    "Settings": "Impostazioni",
    "Settings…": "Impostazioni…",
    "Appearance": "Aspetto",
    "System": "Come il sistema",
    "Light": "Chiaro",
    "Dark": "Scuro",
    "Language": "Lingua",
    "Interface language": "Lingua dell’interfaccia",
    "Restart Ligature now": "Riavvia Ligature ora",
    "Close": "Chiudi",
    "Keyboard shortcuts": "Scorciatoie da tastiera",
    "New ER / UML diagram": "Nuovo diagramma E/R / UML",
    "Open, save, save as": "Apri, salva, salva con nome",
    "Tools: select, entity, relationship, generalisation, class, link":
        "Strumenti: selezione, entità, relazione, generalizzazione, classe, collegamento",
    "Copy, cut, paste (also into another diagram)": "Copia, taglia, incolla (anche in un altro diagramma)",
    "Arrow keys": "Tasti freccia",
    "Move the selection (with Shift, further)": "Sposta la selezione (con Maiusc, più lontano)",
    "Tools: select, entity, relationship, class, link":
        "Strumenti: selezione, entità, relazione, classe, collegamento",
    "Double-click": "Doppio clic",
    "Add an entity or class, or edit the one clicked":
        "Aggiungi un’entità o una classe, oppure modifica quella su cui hai fatto clic",
    "Delete the selection": "Elimina la selezione",
    "Undo / redo": "Annulla / ripeti",
    "Cancel the tool": "Annulla lo strumento",
    "Space + drag, middle button": "Spazio + trascinamento, pulsante centrale",
    "Move around": "Spostarsi",
    "Zoom": "Zoom",
    "Export as PNG, PDF": "Esporta come PNG, PDF",
    "About Ligature": "Informazioni su Ligature",
    "Quit Ligature": "Esci da Ligature",
    "Free software under the GNU General Public License, version 3 or later.":
        "Software libero sotto la GNU General Public License, versione 3 o successiva.",

    # ---- errors
    "Choose where to save the diagram.": "Scegli dove salvare il diagramma.",
    "That entity no longer exists.": "Questa entità non esiste più.",
    "That item is no longer in the diagram.": "Questo elemento non è più nel diagramma.",
    "That file doesn't exist any more.": "Questo file non esiste più.",
    "Couldn't read the file.": "Impossibile leggere il file.",
    "Couldn't save the file there.": "Impossibile salvare il file in quella posizione.",
    "This picture has no Ligature diagram inside it.": "Questa immagine non contiene alcun diagramma di Ligature.",
    "This isn't a Ligature diagram, or it's damaged.":
        "Questo non è un diagramma di Ligature, oppure è danneggiato.",
    "This diagram was made with a newer Ligature. Update Ligature to open it.":
        "Questo diagramma è stato creato con una versione più recente di Ligature. Aggiorna Ligature per aprirlo.",
    "not a Ligature file": "non è un file di Ligature",
    "not a PNG": "non è un PNG",
    "not an SVG": "non è un SVG",
    "a picture is needed to save as PNG or SVG": "serve un’immagine per salvare come PNG o SVG",

    # ---- generalisations, clipboard, warnings
    "Generalisation": "Generalizzazione",
    "Specialisations": "Specializzazioni",
    "Specialisations of {parent}": "Specializzazioni di {parent}",
    "No longer a specialisation": "Non più una specializzazione",
    "Total": "Totale",
    "Partial": "Parziale",
    "Exclusive": "Esclusiva",
    "Overlapping": "Sovrapposta",
    "As tables": "Come tabelle",
    "A table for each (children use the parent's key)":
        "Una tabella per ciascuna (le figlie usano la chiave del genitore)",
    "One table: children merged into the parent": "Una sola tabella: le figlie accorpate nel genitore",
    "A table per child: parent merged into them": "Una tabella per figlia: il genitore accorpato in esse",
    "Total (t): every parent is also one of the children; partial (p): not necessarily. Exclusive (e): at most one child; overlapping (s): maybe several. To add a child, pick Generalisation in the toolbar and click the child, then the parent.":
        "Totale (t): ogni genitore è anche una delle figlie; parziale (p): non necessariamente. "
        "Esclusiva (e): al massimo una figlia; sovrapposta (s): anche più di una. Per aggiungere una "
        "figlia, scegli Generalizzazione nella barra degli strumenti e fai clic sulla figlia, poi sul genitore.",
    "Merging into the children needs a total generalisation whose parent takes part in no relationship.":
        "L’accorpamento nelle figlie richiede una generalizzazione totale il cui genitore non partecipi "
        "ad alcuna relazione.",
    "Click the specialised entity (the child).": "Fai clic sull’entità specializzata (la figlia).",
    "Now click the parent entity. Esc cancels.": "Ora fai clic sull’entità genitore. Esc annulla.",
    "No key: mark its identifier with the key icon.":
        "Nessuna chiave: segna il suo identificatore con l’icona della chiave.",
    "University, with a generalisation (ER)": "Università, con una generalizzazione (E/R)",
    "Cut": "Taglia",
    "Paste": "Incolla",
    "An entity can't be a specialisation of itself.":
        "Un’entità non può essere una specializzazione di se stessa.",
    "That would make a circle of specialisations.": "Si creerebbe un ciclo di specializzazioni.",
    "Those items belong in a different kind of diagram.":
        "Questi elementi appartengono a un altro tipo di diagramma.",
    "“{subject}”'s generalisation is partial, so it can't be merged into its children: it keeps separate tables.":
        "La generalizzazione di “{subject}” è parziale, quindi non può essere accorpata nelle figlie: "
        "mantiene tabelle separate.",
    "“{subject}” takes part in relationships, so its generalisation can't be merged into its children: it keeps separate tables.":
        "“{subject}” partecipa a delle relazioni, quindi la sua generalizzazione non può essere "
        "accorpata nelle figlie: mantiene tabelle separate.",

    # ---- updates
    "Can't reach GitHub to check for updates. Check your internet connection.": 'Impossibile contattare GitHub per cercare aggiornamenti. Controlla la connessione a Internet.',
    'Check for updates…': 'Cerca aggiornamenti…',
    'Check now': 'Controlla ora',
    "Couldn't check for updates": 'Impossibile cercare aggiornamenti',
    "Couldn't start the installer.": "Impossibile avviare l'installazione.",
    'Downloading…': 'Download in corso…',
    'Downloading… {done} of {total} MB': 'Download in corso… {done} di {total} MB',
    'GitHub is limiting update checks right now: try again in an hour.': 'GitHub sta limitando la ricerca di aggiornamenti: riprova tra un’ora.',
    "GitHub sent an answer Ligature doesn't understand.": 'GitHub ha inviato una risposta che Ligature non comprende.',
    'Installing was cancelled.': 'Installazione annullata.',
    'Installing… your system may ask for your password.': 'Installazione… il sistema potrebbe chiederti la password.',
    'Later': 'Più tardi',
    'Ligature {version} is available': 'Ligature {version} è disponibile',
    'No release notes.': 'Nessuna nota di rilascio.',
    'No updates': 'Nessun aggiornamento',
    'Open download page': 'Apri la pagina di download',
    'Skip this version': 'Salta questa versione',
    'Something went wrong: {error}': 'Qualcosa è andato storto: {error}',
    "The download didn't finish. Check your internet connection and try again.": 'Il download non è terminato. Controlla la connessione a Internet e riprova.',
    "The download was damaged (its checksum doesn't match), so it wasn't installed. Try again.": 'Il file scaricato è danneggiato (il checksum non corrisponde), quindi non è stato installato. Riprova.',
    "There's no download for this computer in that release.": 'Questa versione non contiene un file per questo computer.',
    "This copy of Ligature can't update itself (for example when it runs from source). Download the new version from GitHub.": 'Questa copia di Ligature non può aggiornarsi da sola (ad esempio quando viene eseguita dai sorgenti). Scarica la nuova versione da GitHub.',
    "This copy of Ligature can't update itself.": 'Questa copia di Ligature non può aggiornarsi da sola.',
    'Update available': 'Aggiornamento disponibile',
    'Update now': 'Aggiorna ora',
    'Updates': 'Aggiornamenti',
    'You have the latest version of Ligature ({version}).': 'Hai l’ultima versione di Ligature ({version}).',
    "You have {version}. Here's what's new:": 'Hai la versione {version}. Ecco le novità:',
    'Check for new versions once a day': 'Cerca nuove versioni una volta al giorno',
    'You have version {version}.': 'Hai la versione {version}.',
    "{page}: start or open a diagram first": "{page}: crea o apri prima un diagramma",
}

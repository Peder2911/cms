function refresh(page) {
   fetch(`/api/content?page=?{page}`)
      .then((response) => response.json())
      .then((data) => {
         posts.innerHTML = ""
         data.entries.forEach(entry => {
            el = document.createElement("li")
            let link = document.createElement("a")
            link.innerText = `${entry.title} @ ${entry.created}`
            link.href = `/entries/${entry.title}`

            el.appendChild(link)
            posts.appendChild(el)
         })
      })
}

refresh()

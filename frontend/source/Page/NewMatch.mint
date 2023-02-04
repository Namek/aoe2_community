component Page.NewMatch {
  const GROUPS = ["Mecze Rotacyjne", "Gold", "Red", "Black", "Blue", "Green"]

  const MAPS_GOLD =
    [
      "Acropolakes",
      "Coast to Mountain",
      "Ghost Lake",
      "Glacier Lagoon",
      "Golden Pit",
      "Graveyards",
      "Ring of Reeds",
      "Siberian Crater"
    ]

  const MAPS_RED =
    [
      "Acropolakes",
      "Coast to Mountain",
      "Ghost Lake",
      "Glacier Lagoon",
      "Golden Pit",
      "Graveyards",
      "Ring of Reeds",
      "Siberian Crater"
    ]

  const MAPS_BLACK =
    [
      "Acropolakes",
      "Ghost Lake",
      "Glacier Lagoon",
      "Graveyards",
      "Ring of Reeds",
      "Siberian Crater"
    ]

  const MAPS_BLUE =
    [
      "Acropolakes",
      "Cattails",
      "Ghost Lake",
      "Graveyards",
      "Glacier Lagoon",
      "Siberian Crater"
    ]

  const MAPS_GREEN =
    [
      "Acropolis",
      "Golden Pit",
      "Hideout",
      "Siberian Crater",
      "Socotra"
    ]

  const MAPS_ROTATION =
    [
      "Golden Pit",
      "Hideout"
    ]

  const ALL_CIVS =
    [
      "Aztecs",
      "Bengalis",
      "Berbers",
      "Bohemians",
      "Britons",
      "Bulgarians",
      "Burgundians",
      "Burmese",
      "Byzantines",
      "Celts",
      "Chinese",
      "Cumans",
      "Dravidians",
      "Ethiopians",
      "Franks",
      "Goths",
      "Gurjaras",
      "Hindustani",
      "Huns",
      "Incas",
      "Italians",
      "Japanese",
      "Khmer",
      "Koreans",
      "Lithuanians",
      "Magyars",
      "Malay",
      "Malians",
      "Mayans",
      "Mongols",
      "Persians",
      "Poles",
      "Portuguese",
      "Saracens",
      "Sicilians",
      "Slavs",
      "Spanish",
      "Teutons",
      "Tatars",
      "Turks",
      "Vietnamese",
      "Vikings"
    ]

  state selectedGroup = ""
  state maxRecordingsAmount = 3
  state collectedRecordingFiles : Map(Number, File) = Map.empty()
  state isFormValid = false
  state wasFormSubmitted = false
  state invalidFields : Array(String) = []

  fun componentDidMount {
    void
  }

  fun maximumGamesAmount (group : String) {
    case (group) {
      "Red" => 5
      "Gold" => 5
      => 3
    }
  }

  get minimumRecordingsAmount {
    (maximumGamesAmount(selectedGroup) + 1) / 2
  }

  get minimumMapsPickedByPlayer {
    /* minus one, because without Arabia */
    (maximumGamesAmount(selectedGroup) / 2) - 1
  }

  get maps {
    case (selectedGroup) {
      "Gold" => MAPS_GOLD
      "Red" => MAPS_RED
      "Black" => MAPS_BLACK
      "Blue" => MAPS_BLUE
      "Green" => MAPS_GREEN
      "Mecze Rotacyjne" => MAPS_ROTATION
      => []
    }
  }

  get civDraftEnabled {
    case (selectedGroup) {
      "Mecze Rotacyjne" => false
      => true
    }
  }

  get civBansCount {
    case (selectedGroup) {
      "Mecze Rotacyjne" => 0
      => 0
    }
  }

  get mapBanEnabled {
    Array.size(maps) > 2
  }

  fun moreRecordings (evt : Html.Event) {
    sequence {
      next { maxRecordingsAmount = maxRecordingsAmount + 1 }
    }
  }

  fun onGroupSelect (evt : Html.Event) {
    try {
      group =
        `#{evt.target}.value`

      next
        {
          selectedGroup = group,
          maxRecordingsAmount = maximumGamesAmount(group)
        }
    }
  }

  fun onSetRecordingFile (index : Number, evt : Html.Event) {
    try {
      files =
        `#{evt.target}.files` as Array(File)

      file =
        files[0]
        |> Debug.log

      next
        {
          collectedRecordingFiles =
            case (file) {
              Maybe::Just(f) =>
                Map.set(index, f, collectedRecordingFiles)

              Maybe::Nothing => Map.delete(index, collectedRecordingFiles)
            }
        }
    }
  }

  fun validateForm {
    sequence {
      next
        {
          invalidFields = Debug.log(validateFormData(`new FormData(document.forms[0])`)),
          isFormValid = Array.isEmpty(invalidFields)
        }
    }
  }

  fun validateFormData (formData : FormData) {
    try {
      values =
        `(() => {
          const map = new Map()
          for (const [key, val] of #{formData}) {
            const isCorrectValue = typeof val == 'object' ? val.size > 0 : !!val

            if (key.endsWith("[]")) {
              map[key] = [...(map[key] || []), ...(isCorrectValue ? [val] : [])]
            }
            else {
              map[key] = isCorrectValue ? val : null
            }
          }
          return map
        })()
        `

      invalidFields =
        `(() => {
          const invalidFields = []
          for (const key in #{values}) {
            const val = #{values}[key]
            let isInvalid = val === null

            if (!isInvalid) {
              if (key === "recording_files[]") {
                isInvalid = val.length < #{minimumRecordingsAmount}
              } else if (key === "p0_maps[]" || key === "p1_maps[]") {
                isInvalid = val.length < #{minimumMapsPickedByPlayer} || (new Set(val)).size !== val.length
              } else if (key == "p0_civ_bans[]" || key == "p1_civ_bans[]") {
                isInvalid = val.length < #{civBansCount} || (new Set(val)).size !== val.length
              } else if (key === "civ_draft") {
                isInvalid = !/^(https:\/\/aoe2cm.net\/draft\/)?[A-Za-z0-9]{5}$/.test(val)
              }
            }

            if (isInvalid) {
              invalidFields.push(key)
            }
          }

          return invalidFields
        })()
        ` as Array(String)

      invalidFields
    }
  }

  fun onFormChange (evt : Html.Event) {
    sequence {
      `#{evt.event}.preventDefault()`
      validateForm()
    }
  }

  fun onSubmit (evt : Html.Event) {
    sequence {
      `#{evt.event}.preventDefault()`
      App.setLoading(true)

      case (matchForm) {
        Maybe::Just(form) =>
          try {
            formData =
              (`new FormData(document.forms[0])`)

            invalidFields =
              validateFormData(formData)

            isFormValid =
              Array.isEmpty(invalidFields)

            next
              {
                invalidFields = invalidFields,
                isFormValid = isFormValid,
                wasFormSubmitted = true
              }

            if (!isFormValid) {
              `alert('Błąd: braki w formularzu!')`
            } else {
              sequence {
                files =
                  (`#{formData}.getAll('recording_files[]')` as Array(File))
                  |> Array.select((f : File) { File.size(f) > 0 })

                bestOf =
                  maximumGamesAmount(selectedGroup)

                `(() => {
                  for (const file of #{files}) {
                    #{formData}.append("recording_times[]", file.lastModified)
                  }

                  #{formData}.set('best_of', #{bestOf})
                })()`

                /* fix for FastAPI: remove "[]" from variable names */
                finalFormData =
                  `(() => {
                    const newFormData = new FormData()
                    console.log('allkeys', new Set(#{formData}.keys()))
                    for (const key of new Set(#{formData}.keys())) {
                      if (key.endsWith("[]")) {
                        const newKey = key.slice(0, -2)
                        const arr = #{formData}.getAll(key)
                        console.log(arr)
                        for (const val of arr) {
                          newFormData.append(newKey, val)
                        }
                      } else {
                        newFormData.set(key, #{formData}.get(key))
                      }
                    }

                    return newFormData
                  })()
                  ` as FormData

                response =
                  Http.post("#{@ENDPOINT}/api/match")
                  |> Http.formDataBody(finalFormData)
                  |> Http.send()

                Debug.log(response)

                case (Utils.decodeServerError(response.body)) {
                  Maybe::Just(err) => `alert(#{err})`

                  =>
                    if (response.status == 200) {
                      sequence {
                        err =
                          `alert('Mecz zapisany, dzięki!')`

                        `#{form}.reset()`

                        Window.navigate("/#matches")
                      }
                    } else {
                      `alert("Błąd serwera: " + #{response}.status)`
                    }
                }
              } catch Http.ErrorResponse => error {
                `alert(JSON.stringify(#{error}))`
              }
            }
          }

        Maybe::Nothing => void
      }

      App.setLoading(false)
    }
  }

  fun markFieldError (fieldName : String) {
    wasFormSubmitted && Array.contains(fieldName, invalidFields)
  }

  fun render : Html {
    <form::main as matchForm onChange={onFormChange}>
      <h2 class="subtitle">
        "Wrzuć nagrania z meczu"
      </h2>

      <div class="columns">
        <div class="column">
          <div class="field">
            <label class="label">
              "Grupa"
            </label>

            <div class="control">
              <select
                type="text"
                class="input #{Utils.whenStr(markFieldError("group"), "is-danger")}"
                name="group"
                onChange={onGroupSelect}
                value={selectedGroup}>

                <option>"-- Grupa (poziom) --"</option>

                for (opt of GROUPS) {
                  <option value={opt}>
                    "#{opt} (BO#{maximumGamesAmount(opt)})"
                  </option>
                }

              </select>
            </div>
          </div>

          if (civDraftEnabled) {
            <div class="field">
              <label class="label">
                "Civ Draft: link lub kod"
              </label>

              <div class="control">
                <input
                  class="input #{Utils.whenStr(markFieldError("civ_draft"), "is-danger")}"
                  type="text"
                  name="civ_draft"
                  required="true"
                  placeholder="np. WXfmK lub https://aoe2cm.net/draft/WXfmK"/>
              </div>
            </div>
          }

          <div class="field">
            <label class="label">
              "Data"

              <div class="control">
                <input
                  type="date"
                  class="input #{Utils.whenStr(markFieldError("group"), "is-danger")}"
                  name="date"/>
              </div>
            </label>
          </div>
        </div>

        <div class="column">
          <div class="columns">
            <{ renderPlayer(0, "Gracz A (Ty)") }>
            <{ renderPlayer(1, "Gracz B (przeciwnik)") }>
          </div>
        </div>
      </div>

      <div>
        <div class="field">
          <label class="label">
            "Pliki nagrań (minimum #{minimumRecordingsAmount})"
          </label>

          <p>"Jeśli gra została przerwana i musieliście ją kontynuować przy użyciu funkcji \"Restore\" to wrzuć zarówno kawałek nagrania przed przerwą jak i po."</p>

          <div class="column">
            for (i of Array.range(0, maxRecordingsAmount - 1)) {
              try {
                filename =
                  Map.get(i, collectedRecordingFiles)
                  |> Maybe.map((file : File) { File.name(file) })

                <div
                  class={
                    "file has-name is-fullwidth
                    #{Utils.whenStr(filename != Maybe::Nothing, "is-primary")}
                    #{Utils.whenStr(markFieldError("recording_files[]"), "is-danger")}"
                  }
                  key={Number.toString(i)}>

                  <label class="file-label">
                    <input
                      class="file-input"
                      type="file"
                      accept=".aoe2record"
                      name="recording_files[]"
                      onChange={onSetRecordingFile(i)}/>

                    <span class="file-cta">
                      <span class="file-icon">
                        <i class="fas fa-upload"/>
                      </span>

                      <span class="file-label">
                        "Wybierz plik…"
                      </span>
                    </span>

                    <span class="file-name">
                      <{ filename or "Nagranie #{i + 1}" }>
                    </span>
                  </label>

                </div>
              }
            }

            <button
              class="button is-small is-info"
              type="button"
              onClick={moreRecordings}>

              "+"

            </button>
          </div>
        </div>

        <hr/>

        <div class="field has-addons is-justify-content-flex-end">
          <div class="control">
            <input
              type="password"
              class="input #{Utils.whenStr(markFieldError("password"), "is-danger")}"
              name="password"
              placeholder="Twoje prywatne hasło"/>
          </div>

          <div class="control">
            <button
              type="submit"
              class="button is-primary"
              onClick={onSubmit}>

              "Wyślij"

            </button>
          </div>
        </div>
      </div>
    </form>
  }

  fun renderPlayer (playerIndex : Number, label : String) : Html {
    <div class="column">
      <div class="field">
        <label class="label">
          <{ label }>
        </label>

        <div class="control has-icons-left">
          try {
            name =
              "p#{playerIndex}_name"

            <input
              type="text"
              class="input #{Utils.whenStr(markFieldError(name), "is-danger")}"
              name={name}
              placeholder="ksywa"/>
          }

          <span class="icon is-small is-left">
            <i class="fas fa-user"/>
          </span>
        </div>
      </div>

      if (mapBanEnabled) {
        <div class="field">
          <div class="control">
            try {
              name =
                "p#{playerIndex}_map_ban"

              <div class="select is-fullwidth #{Utils.whenStr(markFieldError(name), "is-danger")}">
                <select
                  name={name}
                  disabled={Array.isEmpty(maps)}>

                  <option>"-- Ban Mapy --"</option>

                  for (map of maps) {
                    <option value={map}>
                      "#{map}"
                    </option>
                  }

                </select>
              </div>
            }
          </div>
        </div>
      }

      for (i of Array.range(1, minimumMapsPickedByPlayer + 1)) {
        <div class="field">
          <div class="control">
            try {
              name =
                "p#{playerIndex}_maps[]"

              <div class="select is-fullwidth #{Utils.whenStr(markFieldError(name), "is-danger")}">
                <select
                  name={name}
                  disabled={Array.isEmpty(maps)}>

                  <option>"-- Mapa #{i + 1}. --"</option>

                  for (map of maps) {
                    <option value={map}>
                      "#{map}"
                    </option>
                  }

                </select>
              </div>
            }
          </div>
        </div>
      }

      if (civBansCount > 0) {
        for (i of Array.range(0, civBansCount - 1)) {
          <div class="field">
            <div class="control">
              try {
                name =
                  "p#{playerIndex}_civ_bans[]"

                <div class="select is-fullwidth #{Utils.whenStr(markFieldError(name), "is-danger")}">
                  <select name={name}>
                    <option>"-- Ban Civ #{i + 1}. --"</option>

                    for (civ of ALL_CIVS) {
                      <option value={civ}>
                        "#{civ}"
                      </option>
                    }
                  </select>
                </div>
              }
            </div>
          </div>
        }
      }
    </div>
  }

  style main {
    max-width: 900px;
    margin: 0 auto;
  }
}

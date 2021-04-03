store Matches {
  state matches : Maybe(Result(String, Array(Match))) = Maybe::Nothing

  fun refreshList {
    sequence {
      App.setLoading(true)

      response =
        "#{@ENDPOINT}/api/matches"
        |> Http.get()
        |> Http.send()

      matches =
        response.body
        |> Json.parse
        |> Maybe.map(
          (json : Object) {
            decode json as Array(Match)
            |> Result.mapError((err : Object.Error) { "Błąd dekodowania." })
          })

      next { matches = Debug.log(matches) }

      App.setLoading(false)
    } catch Http.ErrorResponse => error {
      try {
        next
          {
            matches =
              Maybe::Just(
                Result.error(
                  case (error.type) {
                    Http.Error::NetworkError =>
                      "Błąd połączenia z serwerem."

                    => "Wewnętrzny błąd serwera."
                  }
                  |> Debug.log))
          }

        App.setLoading(false)
      }
    }
  }
}

record Match {
  matchId : Number using "id",
  group : String,
  civDraft : String using "civ_draft",
  date : Number,
  bestOf : Number using "best_of",
  p0Name : String using "p0_name",
  p1Name : String using "p1_name",
  p0MapBan : String using "p0_map_ban",
  p1MapBan : String using "p1_map_ban",
  p0Maps : Array(String) using "p0_maps",
  p1Maps : Array(String) using "p1_maps",
  recordings : Array(Recording)
}

record Recording {
  id : Number,
  gameVersion : String using "game_version"
}

component Page.Matches {
  connect Matches exposing { matches }

  fun componentDidMount {
    Matches.refreshList()
  }

  fun render : Html {
    <div::app>
      case (matches) {
        Maybe::Just result =>
          case (result) {
            Result::Ok ms =>
              if (Array.size(ms) == 0) {
                <p>"Brak meczy."</p>
              } else {
                <table class="table is-hoverable is-narrow">
                  <thead>
                    <tr>
                      <th>"Data"</th>
                      <th>"Grupa"</th>
                      <th>"Draft"</th>
                      <th>"Nagrania"</th>
                    </tr>
                  </thead>

                  <tbody>
                    for (match of ms) {
                      <tr>
                        <td>"#{Utils.epochToDateString(match.date)}"</td>
                        <td>"#{match.group} (BO#{match.bestOf})"</td>

                        <td>
                          <{ renderDraft(match) }>
                        </td>

                        <td>
                          for (rec of match.recordings
                          |> Array.mapWithIndex((rec : Recording, i : Number) { {rec, i} })) {
                            <>
                              <a href="#{@ENDPOINT}/api/match/#{match.matchId}/recording/#{rec[0].id}">
                                "##{rec[1] + 1}"
                              </a>

                              " "
                            </>
                          }
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              }

            Result::Err err =>
              <p>
                <{ err }>
              </p>
          }

        Maybe::Nothing => <p>"Ładowanie..."</p>
      }
    </div>
  }

  fun renderDraft (match : Match) : Html {
    <table::draft class="table is-bordered is-narrow is-fullwidth is-striped">
      <thead>
        <tr>
          <td>
            <a
              href="https://aoe2cm.net/draft/#{match.civDraft}"
              target="_blank">

              "Civ Draft"

            </a>
          </td>

          <td>"#{match.p0Name}"</td>
          <td>"#{match.p1Name}"</td>
        </tr>
      </thead>

      <tbody>
        <tr>
          <th>"ban"</th>
          <td>"#{match.p0MapBan}"</td>
          <td>"#{match.p1MapBan}"</td>
        </tr>

        <tr>
          <th>"home mapy"</th>

          <td>"#{match.p0Maps
            |> String.join(", ")}"</td>

          <td>"#{match.p1Maps
            |> String.join(", ")}"</td>
        </tr>
      </tbody>
    </table>
  }

  style app {
    display: flex;
    justify-content: center;

    table {
      margin: 0 auto;
    }
  }

  style draft {
    tr > * {
      width: 33%;
    }
  }
}

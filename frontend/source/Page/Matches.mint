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

      matches
    } catch Http.ErrorResponse => error {
      try {
        matches =
          Maybe::Just(
            Result.error(
              case (error.type) {
                Http.Error::NetworkError =>
                  "Błąd połączenia z serwerem."

                => "Wewnętrzny błąd serwera."
              }
              |> Debug.log))

        next { matches = matches }

        matches
      }
    } finally {
      App.setLoading(false)
    }
  }

  fun deleteMatch (match : Match) {
    sequence {
      title =
        "#{match.p0Name} vs #{match.p1Name}"

      ret =
        `window.confirm("Czy na pewno chcesz usunąć mecz #{title}?")` as Bool

      if (ret) {
        sequence {
          App.setLoading(true)

          /* |> Http.formDataBody(FormData.empty()) */
          response =
            "#{@ENDPOINT}/api/match/#{match.id}"
            |> Http.delete()
            |> Http.withCredentials(true)
            |> Http.send()

          refreshList()

          void
        } catch Http.ErrorResponse => error {
          `alert("Sromotna klęska: " + JSON.stringify(#{error}))`
        }
      } else {
        Promise.never()
      }

      App.setLoading(false)
    }
  }

  fun toggleWatched (match : Match) {
    sequence {
      refreshList()

      updatedMatches =
        (matches or Result::Ok([]))
        |> Result.withDefault([])

      case (Array.find((m : Match) { m.id == match.id }, updatedMatches)) {
        Maybe::Just(updatedMatch) =>
          sequence {
            patch =
              { watched = !updatedMatch.watched }

            response =
              Http.empty()
              |> Http.url("#{@ENDPOINT}/api/match/#{match.id}")
              |> Http.method("PATCH")
              |> Http.withCredentials(true)
              |> Http.jsonBody(encode patch)
              |> Http.send()

            next
              {
                matches =
                  updatedMatches
                  |> Array.map(
                    (m : Match) {
                      if (m.id == match.id) {
                        { m | watched = patch.watched }
                      } else {
                        m
                      }
                    })
                  |> Result.ok
                  |> Maybe.just
              }

            void
          } catch Http.ErrorResponse => error {
            sequence {
              `alert("Sromotna klęska: " + JSON.stringify(#{error}))`
            }
          }

        =>
          try {
            `alert("Mecz zniknął z listy.")`
          }
      }

      void
    }
  }
}

record Match {
  id : Number using "id",
  group : String,
  civDraft : Maybe(String) using "civ_draft",
  date : Number,
  bestOf : Number using "best_of",
  p0Name : String using "p0_name",
  p1Name : String using "p1_name",
  p0MapBan : Maybe(String) using "p0_map_ban",
  p1MapBan : Maybe(String) using "p1_map_ban",
  p0Maps : Array(String) using "p0_maps",
  p1Maps : Array(String) using "p1_maps",
  p0CivBans : Array(String) using "p0_civ_bans",
  p1CivBans : Array(String) using "p1_civ_bans",
  recordings : Array(Recording),
  watched : Bool
}

record MatchPatch {
  watched : Bool
}

record Recording {
  id : Number,
  gameVersion : String using "game_version"
}

enum SortingMode {
  DateDesc
  DateAsc
  Id
}

component Page.Matches {
  connect App exposing { loggedInUser }
  connect Matches exposing { matches }

  state sortingMode = SortingMode::DateDesc

  fun componentDidMount {
    Matches.refreshList()
  }

  fun toggleSortMode {
    next
      {
        sortingMode =
          case (sortingMode) {
            SortingMode::DateDesc => SortingMode::DateAsc
            SortingMode::DateAsc => SortingMode::Id
            SortingMode::Id => SortingMode::DateDesc
          }
      }
  }

  fun matchSortFn (m1 : Match, m2 : Match) {
    case (sortingMode) {
      SortingMode::Id => 0

      SortingMode::DateAsc =>
        m1.date - m2.date

      SortingMode::DateDesc =>
        m2.date - m1.date
    }
  }

  fun render : Html {
    <div::app>
      case (matches) {
        Maybe::Just(result) =>
          case (result) {
            Result::Ok(ms) =>
              if (Array.size(ms) == 0) {
                <p>"Brak meczy."</p>
              } else {
                <table class="table is-hoverable is-narrow">
                  <thead>
                    <tr>
                      <th onClick={toggleSortMode}>
                        "Data "

                        if (sortingMode == SortingMode::DateAsc) {
                          "↓"
                        }

                        if (sortingMode == SortingMode::DateDesc) {
                          "↑"
                        }
                      </th>

                      <th>"Grupa"</th>
                      <th>"Draft"</th>
                      <th>"Nagrania"</th>

                      if (App.hasAdminRole) {
                        <th/>
                      }
                    </tr>
                  </thead>

                  <tbody>
                    for (match of Array.sort(matchSortFn, ms)) {
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
                              <a
                                href="#{@ENDPOINT}/api/match/#{match.id}/recording/#{rec[0].id}"
                                target="_blank"
                                rel="noopener noreferrer">

                                "##{rec[1] + 1}"

                              </a>

                              " "
                            </>
                          }
                        </td>

                        if (App.hasAdminRole) {
                          <td>
                            <label class="checkbox">
                              <input
                                type="checkbox"
                                checked={match.watched}
                                onChange={(evt : Html.Event) { Matches.toggleWatched(match) }}/>

                              " Skomentowane"
                            </label>

                            <br/>
                            <br/>

                            <button
                              class="button is-danger is-small"
                              onClick={() { Matches.deleteMatch(match) }}>

                              <span>"Usuń mecz"</span>

                            </button>
                          </td>
                        }
                      </tr>
                    }
                  </tbody>
                </table>
              }

            Result::Err(err) =>
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
            if (String.isNotBlank(civDraft)) {
              <a
                href="https://aoe2cm.net/draft/#{civDraft}"
                rel="noopener noreferrer"
                target="_blank">

                "Civ Draft"

              </a>
            }
          </td>

          <td>"#{match.p0Name}"</td>
          <td>"#{match.p1Name}"</td>
        </tr>
      </thead>

      <tbody>
        if (String.isNotBlank(p0MapBan) || String.isNotBlank(p1MapBan)) {
          <tr>
            <th>"map ban"</th>
            <td>"#{p0MapBan}"</td>
            <td>"#{p1MapBan}"</td>
          </tr>
        }

        <tr>
          <th>"home mapy"</th>

          <td>
            "#{match.p0Maps
            |> String.join(", ")}"
          </td>

          <td>
            "#{match.p1Maps
            |> String.join(", ")}"
          </td>
        </tr>

        if (!Array.isEmpty(match.p0CivBans)) {
          <tr>
            <th>"civ bans"</th>

            <td>
              "#{match.p0CivBans
              |> String.join(", ")}"
            </td>

            <td>
              "#{match.p1CivBans
              |> String.join(", ")}"
            </td>
          </tr>
        }
      </tbody>
    </table>
  } where {
    civDraft =
      match.civDraft or ""

    p0MapBan =
      match.p0MapBan or ""

    p1MapBan =
      match.p1MapBan or ""
  }

  style app {
    display: flex;
    justify-content: center;

    table {
      margin: 0 auto;

      th {
        user-select: none;
      }
    }
  }

  style draft {
    tr > * {
      width: 33%;
    }
  }
}

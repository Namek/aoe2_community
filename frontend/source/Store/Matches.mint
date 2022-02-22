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
  watchStatus : Number using "watch_status"
}

record MatchPatch {
  watchStatus : Number using "watch_status"
}

record Recording {
  id : Number,
  gameVersion : Maybe(String) using "game_version"
}

enum SortingMode {
  DateDesc
  DateAsc
  IdDesc
}

store Matches {
  const WATCH_STATUS_UNTOUCHED = 0
  const WATCH_STATUS_WATCHED = 1
  const WATCH_STATUS_COMMENTED = 2
  const WATCH_STATUS_WATCHED_AND_NOTED = 3
  const WATCH_STATUS_TO_BE_COMMENTED_SOON = 4
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
            |> Result.mapError((err : Object.Error) { "Błąd dekodowania listy meczy." })
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

  fun setWatchStatus (match : Match, newStatus : Number) {
    sequence {
      refreshList()

      updatedMatches =
        (matches or Result::Ok([]))
        |> Result.withDefault([])

      case (Array.find((m : Match) { m.id == match.id }, updatedMatches)) {
        Maybe::Just(updatedMatch) =>
          sequence {
            patch =
              { watchStatus = newStatus }

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
                        { m | watchStatus = patch.watchStatus }
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

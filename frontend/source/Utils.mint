module Utils {
  fun whenStr (condition : Bool, str : String) {
    if (condition) {
      str
    } else {
      " "
    }
  }

  fun epochToDateString (epoch : Number) {
    `new Date(#{epoch} * 1000).toISOString().slice(0, 10)`
  }

  fun decodeServerError (json : String) : Maybe(String) {
    try {
      Json.parse(json)
      |> Maybe.andThen(
        (obj : Object) {
          decode obj as ServerError
          |> Result.map((err : ServerError) { err.error })
          |> Result.toMaybe()
        })
    }
  }
}

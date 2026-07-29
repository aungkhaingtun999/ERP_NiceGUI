    # ==========================================================================
    # SAVE SINGLE SETTING
    # ==========================================================================


    def save_setting(

        self,

        key: str,

        value: Any

    ):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .upsert(

                    {

                        "key":

                            key,


                        "value":

                            str(value)

                    },

                    on_conflict="key"

                )

                .execute()

            )



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message=

                "Save setting failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # SAVE MULTIPLE SETTINGS
    # ==========================================================================


    def save_settings(

        self,

        settings: Dict[str, Any]

    ):


        try:


            payload = [


                {


                    "key":

                        key,


                    "value":

                        str(value)


                }


                for key, value in settings.items()


            ]



            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .upsert(

                    payload,

                    on_conflict="key"

                )

                .execute()

            )



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message=

                "Bulk settings save failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }







    # ==========================================================================
    # DELETE SETTING
    # ==========================================================================


    def delete_setting(

        self,

        key: str

    ):


        try:


            result = (

                self.client

                .table(

                    Tables.SETTINGS

                )

                .delete()

                .eq(

                    "key",

                    key

                )

                .execute()

            )



            return {


                "success":

                    True,


                "data":

                    result.data

            }



        except Exception as e:


            log_error(

                message=

                "Delete setting failed",

                exception=e

            )


            return {


                "success":

                    False,


                "message":

                    str(e)

            }

    # ==========================================================================
    # BOOLEAN HELPER
    # ==========================================================================


    def get_bool(

        self,

        key: str

    ):


        value = self.get_setting(

            key

        )


        if value is None:


            return None



        return (

            str(value)

            .lower()

            in

            (

                "true",

                "1",

                "yes",

                "on"

            )

        )







    # ==========================================================================
    # FLOAT HELPER
    # ==========================================================================


    def get_float(

        self,

        key: str

    ):


        value = self.get_setting(

            key

        )


        if value is None:


            return None



        try:


            return float(

                value

            )


        except Exception:


            return None







    # ==========================================================================
    # INTEGER HELPER
    # ==========================================================================


    def get_int(

        self,

        key: str

    ):


        value = self.get_setting(

            key

        )


        if value is None:


            return None



        try:


            return int(

                value

            )


        except Exception:


            return None







    # ==========================================================================
    # TEXT HELPER
    # ==========================================================================


    def get_text(

        self,

        key: str

    ):


        value = self.get_setting(

            key

        )


        if value is None:


            return None



        return str(

            value

        )
        

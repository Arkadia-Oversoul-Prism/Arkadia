package com.arkadia.console

import android.Manifest
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.content.pm.PackageManager
import android.os.Bundle
import android.text.InputType
import androidx.core.content.FileProvider
import android.media.MediaRecorder
import java.io.File
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity:AppCompatActivity(){
        private val identity by lazy { FirebaseIdentity.initialize(this) }
    private val repo by lazy{ConsoleRepository({"https://arkadia-kw64.onrender.com"},{ identity?.idToken(false) }) }
    private lateinit var connection:TextView
    private lateinit var objectList:LinearLayout
    private lateinit var detailType:TextView
    private lateinit var detailTitle:TextView
    private lateinit var detailSummary:TextView
    private lateinit var detailState:TextView
    private lateinit var actionRow:LinearLayout
    private var snap=FieldSnapshot(emptyList(),emptyList(),0,false)
    private var selected:FieldObject?=null
    private val captures by lazy{CaptureStore(this)}
    private var recorder:MediaRecorder?=null
    private var activeVoice:Pair<String,File>?=null
    private var activeCamera:Pair<String,File>?=null

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        val firebase=identity
        if(firebase==null){
            showAuthScreen("Firebase is not configured in this APK.")
        }else if(firebase.currentUser==null){
            showAuthScreen()
        }else{
            showMainScreen()
        }
    }

    private fun bindMainViews(){
        connection=findViewById(R.id.connection)
        objectList=findViewById(R.id.objectList)
        detailType=findViewById(R.id.detailType)
        detailTitle=findViewById(R.id.detailTitle)
        detailSummary=findViewById(R.id.detailSummary)
        detailState=findViewById(R.id.detailState)
        actionRow=findViewById(R.id.actionRow)
        findViewById<Button>(R.id.fieldButton).setOnClickListener{mode("FIELD")}
        findViewById<Button>(R.id.focusButton).setOnClickListener{mode("FOCUS")}
        findViewById<Button>(R.id.deepButton).setOnClickListener{mode("DEEP")}
        findViewById<Button>(R.id.captureButton).setOnClickListener{capture()}
        findViewById<Button>(R.id.askButton).setOnClickListener{ask()}
        findViewById<Button>(R.id.verifyButton).setOnClickListener{load()}
        findViewById<TextView>(R.id.eyebrow).setOnClickListener{authDialog()}
    }

    private fun showMainScreen(){
        setContentView(R.layout.activity_main)
        bindMainViews()
        connection.text="● LIVE · "+(identity?.currentUser?.email ?: "NO IDENTITY")
        load()
    }

    private fun showAuthScreen(error:String?=null){
        setContentView(R.layout.activity_auth)
        val email=findViewById<EditText>(R.id.authEmail)
        val password=findViewById<EditText>(R.id.authPassword)
        val message=findViewById<TextView>(R.id.authMessage)
        if(error!=null) message.text=error
        findViewById<Button>(R.id.signInButton).setOnClickListener{
            authenticate(email.text.toString(),password.text.toString(),false)
        }
        findViewById<Button>(R.id.registerButton).setOnClickListener{
            authenticate(email.text.toString(),password.text.toString(),true)
        }
    }

    private fun authenticate(email:String,password:String,register:Boolean){
        if(email.isBlank() || password.isBlank()){
            Toast.makeText(this,"Email and password are required.",Toast.LENGTH_SHORT).show()
            return
        }
        lifecycleScope.launch{
            runCatching{
                if(register) identity?.register(email,password) ?: error("Firebase is not configured")
                else identity?.signIn(email,password) ?: error("Firebase is not configured")
            }.onSuccess{
                Toast.makeText(this@MainActivity,if(register)"Firebase identity created." else "Firebase identity established.",Toast.LENGTH_SHORT).show()
                showMainScreen()
            }.onFailure{
                Toast.makeText(this@MainActivity,(if(register)"Registration failed: " else "Sign-in failed: ")+it.message,Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun authDialog(){
        val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(32,8,32,0)}
        val email=EditText(this).apply{hint="Email";inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS}
        val password=EditText(this).apply{hint="Password";inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD}
        box.addView(email);box.addView(password)
        val signed=identity?.currentUser
        val dialog=AlertDialog.Builder(this).setTitle(if(signed!=null) "Firebase identity" else "Firebase sign in").setView(box)
        if(signed!=null){
            dialog.setMessage(signed.email ?: signed.uid).setNegativeButton("Sign out"){_,_->identity?.signOut();showAuthScreen()}.setPositiveButton("Close",null)
        }else{
            dialog.setNegativeButton("Cancel",null)
            dialog.setPositiveButton("Sign in"){_,_->lifecycleScope.launch{runCatching{identity?.signIn(email.text.toString(),password.text.toString()) ?: error("Firebase not configured")}.onSuccess{Toast.makeText(this@MainActivity,"Firebase identity established.",Toast.LENGTH_SHORT).show();load()}.onFailure{Toast.makeText(this@MainActivity,"Firebase sign-in failed: "+it.message,Toast.LENGTH_LONG).show()}}}
            dialog.setNeutralButton("Register"){_,_->lifecycleScope.launch{runCatching{identity?.register(email.text.toString(),password.text.toString()) ?: error("Firebase not configured")}.onSuccess{Toast.makeText(this@MainActivity,"Firebase identity created.",Toast.LENGTH_SHORT).show();load()}.onFailure{Toast.makeText(this@MainActivity,"Firebase registration failed: "+it.message,Toast.LENGTH_LONG).show()}}}
        }
        dialog.show()
    }
    private fun load(){
        connection.text="● READING"
        lifecycleScope.launch{
            snap=repo.snapshot()
            connection.text=if(snap.live)"● LIVE · "+(identity?.currentUser?.email ?: "NO IDENTITY") else "● UNAVAILABLE"
            render()
            if(!snap.live)Toast.makeText(this@MainActivity,snap.message?:"Oracle unavailable",Toast.LENGTH_LONG).show()
        }
    }
    private fun render(){
        objectList.removeAllViews()
        if(snap.objects.isEmpty()){objectList.addView(TextView(this).apply{text="The field has no readable objects yet. This is not an invented empty state.";setTextColor(getColor(R.color.arkadia_muted));textSize=14f;setPadding(12,24,12,24)})}
        snap.objects.forEach{obj->
            val card=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(18,16,18,16);setBackgroundResource(R.drawable.bg_panel)}
            card.addView(TextView(this).apply{text=obj.type+"  •  "+obj.state;setTextColor(getColor(R.color.arkadia_accent));textSize=11f})
            card.addView(TextView(this).apply{text=obj.title;setTextColor(getColor(R.color.arkadia_text));textSize=18f;setTypeface(typeface,android.graphics.Typeface.BOLD)})
            card.addView(TextView(this).apply{text=obj.summary;setTextColor(getColor(R.color.arkadia_muted));textSize=13f;setPadding(0,6,0,0)})
            card.setOnClickListener{focus(obj)}
            objectList.addView(card,LinearLayout.LayoutParams(-1,-2).apply{setMargins(0,0,0,10)})
        }
        selected?.let{focus(it)}?:run{detailType.text="FIELD";detailTitle.text="Nothing selected";detailSummary.text="Tap an object to enter FOCUS. DEEP keeps canonical source and state visible.";detailState.text="CAN ≠ MAY ≠ DID";actionRow.removeAllViews()}
    }
    private fun focus(obj:FieldObject){selected=obj;detailType.text=obj.type+"  •  "+obj.source;detailTitle.text=obj.title;detailSummary.text=obj.summary;detailState.text="STATE: "+obj.state+"\nCAN ≠ MAY ≠ DID\n"+if(obj.authorizationId!=null)"AUTHORIZATION: "+obj.authorizationId else "AUTHORIZATION: NONE";actionRow.removeAllViews()
        if(obj.type=="PROPOSAL"){
            if(obj.state=="ACCEPTED" && obj.authorizationId==null) addAction("AUTHORIZE"){authorize(obj.id)}
            else if(obj.authorizationId==null) addAction("ACCEPT"){decide(obj.id,"ACCEPTED")}
            addAction("DECLINE"){decide(obj.id,"DECLINED")}
            if(obj.authorizationId!=null){
                addAction("EXECUTION ATTEMPT"){execution(obj)}
            }
        }
        if(obj.type=="SIGNAL"||obj.type=="WORK"||obj.type=="KNOWLEDGE")addAction("ASK ARKANA"){ask("Interrogate this "+obj.type+": "+obj.title+"\n"+obj.summary)}
    }
    private fun authorize(id:String){
        lifecycleScope.launch{
            val result=runCatching{repo.authorize(id)}.getOrElse{"Authorization failed: "+it.message}
            Toast.makeText(this@MainActivity,if(result.startsWith("Authorization failed"))result else "HumanAuthorityEvent → Authorization recorded.",Toast.LENGTH_LONG).show()
            load()
        }
    }

    private fun execution(obj:FieldObject){
        val auth=obj.authorizationId ?: return
        val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(24,8,24,0)}
        val tool=EditText(this).apply{hint="Weaver tool channel";setText("git.status");isEnabled=false}
        val payload=EditText(this).apply{hint="Optional tool payload JSON";minLines=3;setText("{}")}
        box.addView(tool);box.addView(payload)
        AlertDialog.Builder(this).setTitle("Governed Weaver execution").setMessage("This dispatches the already-authorized read-only tool through Weaver. The observed result becomes evidence; verification remains your separate act.").setView(box)
            .setNegativeButton("Cancel",null)
            .setPositiveButton("EXECUTE"){_,_->lifecycleScope.launch{
                val response=runCatching{repo.createExecutionAttempt(auth,tool.text.toString().trim(),runCatching{org.json.JSONObject(payload.text.toString())}.getOrElse{org.json.JSONObject().put("description",payload.text.toString())})}.getOrElse{null}
                if(response==null) Toast.makeText(this@MainActivity,"Execution failed: request was not dispatched.",Toast.LENGTH_LONG).show()
                else executionEvidenceDialog(response,obj)
            }}.show()
    }

    private fun executionEvidenceDialog(response:org.json.JSONObject,obj:FieldObject){
        val attempt=response.optJSONObject("execution_attempt")
        val execution=response.optJSONObject("execution")
        val evidence=response.optJSONObject("evidence")
        val evidenceId=evidence?.optString("id").orEmpty()
        val observed=execution?.optString("observed").orEmpty().ifBlank{execution?.toString().orEmpty()}
        val message="Execution: "+(execution?.optString("status")?:"UNKNOWN")+"\\n\\nObserved evidence:\\n"+observed+"\\n\\nEvidence ID: "+evidenceId
        val dialog=AlertDialog.Builder(this).setTitle("Evidence inspector").setMessage(message)
            .setNegativeButton("Close",null)
        if(evidenceId.isNotBlank()) dialog.setPositiveButton("VERIFY"){_,_->verifyDialog(evidenceId,obj)}
        dialog.show()
    }

    private fun verifyDialog(evidenceId:String,obj:FieldObject){
        val input=EditText(this).apply{hint="Claim to verify";setText(obj.title);minLines=3}
        AlertDialog.Builder(this).setTitle("Human verification").setMessage("Choose the verdict. Evidence is observed by Weaver; verification remains yours.").setView(input)
            .setNegativeButton("INSUFFICIENT"){_,_->submitVerification(evidenceId,input.text.toString(),"INSUFFICIENT")}
            .setNeutralButton("CONTRADICTED"){_,_->submitVerification(evidenceId,input.text.toString(),"CONTRADICTED")}
            .setPositiveButton("VERIFIED"){_,_->submitVerification(evidenceId,input.text.toString(),"VERIFIED")}
            .show()
    }

    private fun submitVerification(evidenceId:String,claim:String,verdict:String){
        lifecycleScope.launch{
            val id=runCatching{repo.verify(claim,evidenceId,verdict)}.getOrElse{"Verification failed: "+it.message}
            Toast.makeText(this@MainActivity,if(id.startsWith("Verification failed"))id else "Evidence → "+verdict+" recorded.",Toast.LENGTH_LONG).show()
            load()
        }
    }

    private fun addAction(label:String,action:()->Unit){actionRow.addView(Button(this).apply{text=label;setOnClickListener{action()}})}
    private fun decide(id:String,d:String){lifecycleScope.launch{val msg=runCatching{repo.decide(id,d)}.getOrElse{it.message?:"Decision failed"};Toast.makeText(this@MainActivity,msg,Toast.LENGTH_LONG).show();load()}}
    private fun ask(prefill:String=""){val input=EditText(this).apply{hint="Ask Arkana about what is selected or happening.";setText(prefill);minLines=3};AlertDialog.Builder(this).setTitle("Arkana").setView(input).setNegativeButton("Cancel",null).setPositiveButton("Ask"){_,_->val q=input.text.toString().trim();if(q.isNotBlank())lifecycleScope.launch{val a=runCatching{repo.askArkana(q)}.getOrElse{"Arkana unavailable: "+it.message};AlertDialog.Builder(this@MainActivity).setTitle("Arkana").setMessage(a).setPositiveButton("Close",null).show()}}.show()}
    private fun capture(){
        val labels=arrayOf("VOICE","CAMERA","FILE","OBSERVATION")
        AlertDialog.Builder(this).setTitle("Capture reality").setItems(labels){_,which->when(which){0->voiceCapture();1->cameraCapture();2->fileCapture();3->observationCapture()}}.show()
    }

    private fun voiceCapture(){
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.RECORD_AUDIO),410)
            return
        }
        val pair=captures.newFile("m4a");activeVoice=pair
        try{
            recorder=MediaRecorder(this).apply{
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(pair.second.absolutePath)
                prepare();start()
            }
            AlertDialog.Builder(this).setTitle("Recording voice").setMessage("Reality capture is live. Stop when the observation is complete.")
                .setNegativeButton("Cancel"){_,_->stopVoice(false)}
                .setPositiveButton("Stop & save"){_,_->stopVoice(true)}.show()
        }catch(e:Exception){stopVoice(false);Toast.makeText(this,"Voice capture failed: "+e.message,Toast.LENGTH_LONG).show()}
    }

    private fun stopVoice(save:Boolean){
        val pair=activeVoice
        runCatching{recorder?.stop()}
        recorder?.release();recorder=null;activeVoice=null
        if(save && pair!=null && pair.second.exists() && pair.second.length()>0){
            val record=captures.record(pair.first,"voice",pair.second,"audio/mp4")
            Toast.makeText(this,"Captured "+record.id+" • "+record.sizeBytes+" bytes",Toast.LENGTH_LONG).show()
        }else pair?.second?.delete()
    }

    private fun cameraCapture(){
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.CAMERA),411);return}
        val pair=captures.newFile("jpg");activeCamera=pair
        val uri=FileProvider.getUriForFile(this,packageName+".fileprovider",pair.second)
        startActivityForResult(Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE).apply{putExtra(android.provider.MediaStore.EXTRA_OUTPUT,uri);addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION or Intent.FLAG_GRANT_READ_URI_PERMISSION)},501)
    }

    private fun fileCapture(){
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply{type="*/*";addCategory(Intent.CATEGORY_OPENABLE)},502)
    }

    private fun observationCapture(){
        val input=EditText(this).apply{hint="What did reality say? Record the observation, not an invented interpretation.";minLines=3}
        AlertDialog.Builder(this).setTitle("Capture observation").setView(input).setNegativeButton("Cancel",null).setPositiveButton("Record"){_,_->
            val text=input.text.toString().trim();if(text.isNotBlank())lifecycleScope.launch{val m=runCatching{repo.recordEvent(text)}.getOrElse{"Capture sync failed: "+it.message};Toast.makeText(this@MainActivity,m,Toast.LENGTH_LONG).show()}
        }.show()
    }

    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?){
        super.onActivityResult(requestCode,resultCode,data)
        if(requestCode==501){
            val pair=activeCamera;activeCamera=null
            if(resultCode==RESULT_OK && pair!=null && pair.second.exists()){
                val record=captures.record(pair.first,"camera",pair.second,"image/jpeg")
                Toast.makeText(this,"Captured "+record.id+" • "+record.sha256.take(12)+"…",Toast.LENGTH_LONG).show()
            }else pair?.second?.delete()
        }else if(requestCode==502 && resultCode==RESULT_OK && data?.data!=null){
            val uri=data.data!!;val (id,_)=captures.newFile("bin")
            lifecycleScope.launch{runCatching{captures.copyUri(id,uri,contentResolver.getType(uri) ?: "application/octet-stream",extensionFor(uri))}.onSuccess{Toast.makeText(this@MainActivity,"Captured "+it.id+" • "+it.sizeBytes+" bytes",Toast.LENGTH_LONG).show()}.onFailure{Toast.makeText(this@MainActivity,"File capture failed: "+it.message,Toast.LENGTH_LONG).show()}}
        }
    }

    private fun extensionFor(uri:Uri):String{
        val mime=contentResolver.getType(uri).orEmpty()
        return when{mime.contains("jpeg")||mime.contains("jpg")->"jpg";mime.contains("png")->"png";mime.contains("pdf")->"pdf";mime.contains("audio")->"m4a";mime.contains("video")->"mp4";else->"bin"}
    }

    private fun mode(m:String){findViewById<TextView>(R.id.fieldHint).text=when(m){"FOCUS"->"FOCUS: selected object first. The rest of the field recedes.";"DEEP"->"DEEP: inspect source, state and governed actions. Display remains non-authoritative.";else->"FIELD: what matters now. Live canonical state, not a second database."}}
}

package com.arkadia.console

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.text.InputType
import android.view.ViewGroup
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity:AppCompatActivity(){
    private val prefs by lazy{getSharedPreferences("arkadia_console",Context.MODE_PRIVATE)}
    private val repo by lazy{ConsoleRepository({prefs.getString("api_base","")?:""},{prefs.getString("token","")})}
    private lateinit var connection:TextView
    private lateinit var objectList:LinearLayout
    private lateinit var detailType:TextView
    private lateinit var detailTitle:TextView
    private lateinit var detailSummary:TextView
    private lateinit var detailState:TextView
    private lateinit var actionRow:LinearLayout
    private var snap=FieldSnapshot(emptyList(),emptyList(),0,false)
    private var selected:FieldObject?=null

    override fun onCreate(state:Bundle?){super.onCreate(state);setContentView(R.layout.activity_main)
        connection=findViewById(R.id.connection);objectList=findViewById(R.id.objectList);detailType=findViewById(R.id.detailType);detailTitle=findViewById(R.id.detailTitle);detailSummary=findViewById(R.id.detailSummary);detailState=findViewById(R.id.detailState);actionRow=findViewById(R.id.actionRow)
        findViewById<Button>(R.id.fieldButton).setOnClickListener{mode("FIELD")}
        findViewById<Button>(R.id.focusButton).setOnClickListener{mode("FOCUS")}
        findViewById<Button>(R.id.deepButton).setOnClickListener{mode("DEEP")}
        findViewById<Button>(R.id.captureButton).setOnClickListener{capture()}
        findViewById<Button>(R.id.askButton).setOnClickListener{ask()}
        findViewById<Button>(R.id.verifyButton).setOnClickListener{load()}
        connection.setOnClickListener{connect()}
        if(prefs.getString("api_base","").isNullOrBlank())connect() else load()
    }
    private fun connect(){
        val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(32,8,32,0)}
        val base=EditText(this).apply{hint="https://your-oracle.example";setText(prefs.getString("api_base",""))}
        val token=EditText(this).apply{hint="Firebase ID token / bearer token";setText(prefs.getString("token",""));inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD}
        box.addView(base);box.addView(token)
        AlertDialog.Builder(this).setTitle("Connect Arkadia Console").setMessage("The native console owns backend routing. It will not silently fall back to an unverified deployment.").setView(box).setNegativeButton("Cancel",null).setPositiveButton("Connect"){_,_->prefs.edit().putString("api_base",base.text.toString().trimEnd('/')).putString("token",token.text.toString()).apply();load()}.show()
    }
    private fun load(){if(prefs.getString("api_base","").isNullOrBlank()){connect();return};connection.text="● READING";lifecycleScope.launch{snap=repo.snapshot();connection.text=if(snap.live)"● LIVE" else "● UNAVAILABLE";render();if(!snap.live)Toast.makeText(this@MainActivity,snap.message?:"Oracle unavailable",Toast.LENGTH_LONG).show()}}
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
    private fun focus(obj:FieldObject){selected=obj;detailType.text=obj.type+"  •  "+obj.source;detailTitle.text=obj.title;detailSummary.text=obj.summary;detailState.text="STATE: "+obj.state+"\nCAN ≠ MAY ≠ DID\nDisplay does not authorize execution.";actionRow.removeAllViews()
        if(obj.type=="PROPOSAL"){addAction("ACCEPT"){decide(obj.id,"ACCEPTED")};addAction("DECLINE"){decide(obj.id,"DECLINED")};addAction("WITHDRAW"){decide(obj.id,"WITHDRAWN")}}
        if(obj.type=="SIGNAL"||obj.type=="WORK"||obj.type=="KNOWLEDGE")addAction("ASK ARKANA"){ask("Interrogate this "+obj.type+": "+obj.title+"\n"+obj.summary)}
    }
    private fun addAction(label:String,action:()->Unit){actionRow.addView(Button(this).apply{text=label;setOnClickListener{action()}})}
    private fun decide(id:String,d:String){lifecycleScope.launch{val msg=runCatching{repo.decide(id,d)}.getOrElse{it.message?:"Decision failed"};Toast.makeText(this@MainActivity,msg,Toast.LENGTH_LONG).show();load()}}
    private fun ask(prefill:String=""){val input=EditText(this).apply{hint="Ask Arkana about what is selected or happening.";setText(prefill);minLines=3};AlertDialog.Builder(this).setTitle("Arkana").setView(input).setNegativeButton("Cancel",null).setPositiveButton("Ask"){_,_->val q=input.text.toString().trim();if(q.isNotBlank())lifecycleScope.launch{val a=runCatching{repo.askArkana(q)}.getOrElse{"Arkana unavailable: "+it.message};AlertDialog.Builder(this@MainActivity).setTitle("Arkana").setMessage(a).setPositiveButton("Close",null).show()}}.show()}
    private fun capture(){if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.RECORD_AUDIO),410);Toast.makeText(this,"Microphone permission requested. Native voice capture is next in the capture gate.",Toast.LENGTH_SHORT).show();return};val input=EditText(this).apply{hint="What did reality say? Record the observation, not an invented interpretation.";minLines=3};AlertDialog.Builder(this).setTitle("Capture reality").setView(input).setNegativeButton("Cancel",null).setPositiveButton("Record"){_,_->val q=input.text.toString().trim();if(q.isNotBlank())lifecycleScope.launch{val m=runCatching{repo.recordEvent(q)}.getOrElse{"Capture failed: "+it.message};Toast.makeText(this@MainActivity,m,Toast.LENGTH_LONG).show();load()}}.show()}
    private fun mode(m:String){findViewById<TextView>(R.id.fieldHint).text=when(m){"FOCUS"->"FOCUS: selected object first. The rest of the field recedes.";"DEEP"->"DEEP: inspect source, state and governed actions. Display remains non-authoritative.";else->"FIELD: what matters now. Live canonical state, not a second database."}}
}
